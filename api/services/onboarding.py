"""
Onboarding service - collects user preferences and personalizes ARIA.
"""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.logging import log
from api.db.models import Memory
from api.services import telegram_service


@dataclass
class OnboardingQuestion:
    """A single onboarding question."""
    id: str
    question: str
    type: str  # text, choice, time
    options: list[str] | None = None


ONBOARDING_QUESTIONS = [
    OnboardingQuestion(
        id="name",
        question="What's your name? (This helps me personalize responses)",
        type="text"
    ),
    OnboardingQuestion(
        id="location",
        question="Where do you live? (For weather forecasts)",
        type="text"
    ),
    OnboardingQuestion(
        id="timezone",
        question="What's your timezone?",
        type="choice",
        options=["Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]
    ),
    OnboardingQuestion(
        id="briefing_time",
        question="When would you like your morning briefing? (Format: HH:MM, e.g., 08:00)",
        type="time"
    ),
    OnboardingQuestion(
        id="interests",
        question="What topics interest you? (Comma-separated, e.g., technology, finance, sports)",
        type="text"
    ),
    OnboardingQuestion(
        id="work_hours",
        question="What are your typical work hours? (e.g., 9am-5pm)",
        type="text"
    ),
]


async def start_onboarding(db: AsyncSession) -> None:
    """Start the onboarding flow."""
    # Check if already onboarded
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "user_profile",
            Memory.entity_key == "onboarding_complete"
        )
    )
    
    if result.scalar_one_or_none():
        await telegram_service.send_message("You've already completed onboarding! 🎉")
        return
    
    # Send welcome message
    welcome = """
👋 <b>Welcome to ARIA!</b>

I'm your personal AI assistant. Let me ask you a few questions to personalize your experience.

This will only take a minute! 🚀
"""
    await telegram_service.send_message(welcome)
    
    # Start with first question
    await _send_question(0, db)


async def _send_question(question_index: int, db: AsyncSession) -> None:
    """Send a specific onboarding question."""
    if question_index >= len(ONBOARDING_QUESTIONS):
        await _complete_onboarding(db)
        return
    
    question = ONBOARDING_QUESTIONS[question_index]
    
    # Store current question index
    await _store_onboarding_state(question_index, db)
    
    # Format question
    message = f"<b>Question {question_index + 1}/{len(ONBOARDING_QUESTIONS)}</b>\n\n{question.question}"
    
    # Add options if choice type
    if question.type == "choice" and question.options:
        message += "\n\nOptions:\n"
        for i, option in enumerate(question.options, 1):
            message += f"{i}. {option}\n"
    
    await telegram_service.send_message(message)


async def process_onboarding_answer(
    answer: str,
    db: AsyncSession
) -> None:
    """Process an onboarding answer and move to next question."""
    # Get current question index
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "onboarding_state",
            Memory.entity_key == "current_question"
        )
    )
    state = result.scalar_one_or_none()
    
    if not state:
        await telegram_service.send_message("⚠️ Onboarding session not found. Use /start to begin.")
        return
    
    question_index = int(state.fact)
    question = ONBOARDING_QUESTIONS[question_index]
    
    # Validate and store answer
    if question.type == "choice" and question.options:
        # Handle numeric choice
        if answer.isdigit():
            choice_index = int(answer) - 1
            if 0 <= choice_index < len(question.options):
                answer = question.options[choice_index]
            else:
                await telegram_service.send_message("⚠️ Invalid choice. Please try again.")
                return
    
    # Store answer
    memory = Memory(
        entity_type="user_profile",
        entity_key=question.id,
        fact=answer,
        confidence=1.0,
        source="onboarding"
    )
    db.add(memory)
    await db.flush()
    
    log.info("onboarding_answer_stored", question=question.id, answer=answer)
    
    # Move to next question
    await _send_question(question_index + 1, db)


async def _store_onboarding_state(question_index: int, db: AsyncSession) -> None:
    """Store current onboarding state."""
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "onboarding_state",
            Memory.entity_key == "current_question"
        )
    )
    state = result.scalar_one_or_none()
    
    if state:
        state.fact = str(question_index)
    else:
        state = Memory(
            entity_type="onboarding_state",
            entity_key="current_question",
            fact=str(question_index),
            confidence=1.0,
            source="system"
        )
        db.add(state)
    
    await db.flush()


async def _complete_onboarding(db: AsyncSession) -> None:
    """Complete the onboarding process."""
    # Mark onboarding as complete
    memory = Memory(
        entity_type="user_profile",
        entity_key="onboarding_complete",
        fact="true",
        confidence=1.0,
        source="system"
    )
    db.add(memory)
    
    # Clean up onboarding state
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "onboarding_state"
        )
    )
    for state in result.scalars():
        await db.delete(state)
    
    await db.flush()
    
    # Send completion message
    completion = """
🎉 <b>Onboarding Complete!</b>

Thank you! I've learned about your preferences and will use them to personalize your experience.

You can now:
• Get your morning briefing with /briefing
• Ask me anything naturally
• Check system status with /status

Let's get started! 🚀
"""
    await telegram_service.send_message(completion)
    log.info("onboarding_completed")


async def get_user_profile(db: AsyncSession) -> dict[str, str]:
    """Get user profile from onboarding."""
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "user_profile"
        )
    )
    
    profile = {}
    for memory in result.scalars():
        if memory.entity_key != "onboarding_complete":
            profile[memory.entity_key] = memory.fact
    
    return profile


async def is_onboarded(db: AsyncSession) -> bool:
    """Check if user has completed onboarding."""
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "user_profile",
            Memory.entity_key == "onboarding_complete"
        )
    )
    
    return result.scalar_one_or_none() is not None

# Made with Bob

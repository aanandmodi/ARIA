"""
Telegram update processor worker.
Handles all Telegram updates asynchronously with progressive UI feedback.
NOW WITH CONVERSATION MEMORY AND PERSONAL CONTEXT!
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update

from api.core.config import settings
from api.core.logging import log
from api.core.queue import get_redis
from api.db.models import TelegramSession, UserProfile
from api.db.session import async_session_factory
from api.handlers.reply_handler import handle as handle_reply, handle_callback
from api.handlers.router import dispatch
from api.llm.client import groq_client
from api.llm.intent import IntentResult
from api.llm.intent_unified import parse_intent_unified
from api.llm.personal_context import build_system_prompt
from api.services import telegram_service
from api.services.conversation_service import append_turn, get_history, maybe_compress


WELCOME_MSG = (
    "👋 <b>Welcome to ARIA!</b>\n\n"
    "I'm your personal AI assistant. I'll notify you about important messages "
    "from Gmail, WhatsApp, Discord, Slack, and more.\n\n"
    "Just type naturally — I understand commands like:\n"
    "• <i>remind me about X tomorrow 9am</i>\n"
    "• <i>search emails about project</i>\n"
    "• <i>spent 500 on dinner</i>\n"
    "• <i>play some jazz</i>\n"
    "• <i>check my github PRs</i>\n"
    "• <i>remember that John prefers email</i>\n"
    "• <i>send sms to +91... saying ...</i>\n"
    "• <i>system status</i>\n\n"
    "🚀 ARIA is online and ready!"
)


async def process_telegram_update(ctx: dict, update_dict: dict) -> None:
    """
    Process a Telegram update asynchronously.
    
    This worker provides progressive UI feedback using editMessageText
    to create a "butter smooth" user experience.
    """
    try:
        # Parse the update from dict
        update = Update.de_json(update_dict, telegram_service.get_bot())
        if not update:
            return

        # Route to appropriate handler
        if update.callback_query:
            await _handle_callback_query(update)
        elif update.message and update.message.text:
            await _handle_text_message(update)
        else:
            log.info("telegram_update_ignored", update_type=type(update).__name__)

    except Exception as exc:
        log.error("telegram_processor_failed", error=str(exc))
        try:
            await telegram_service.send_message(
                "⚠️ Something went wrong processing your request."
            )
        except Exception:
            pass


async def _handle_callback_query(update: Update) -> None:
    """Handle inline button callbacks."""
    if not update.callback_query:
        return

    async with async_session_factory() as db:
        try:
            await handle_callback(update.callback_query, db)
            await db.commit()
        except Exception as exc:
            log.error("callback_handler_error", error=str(exc))
            await db.rollback()


async def _handle_text_message(update: Update) -> None:
    """
    Handle text messages with progressive UI feedback.
    
    Flow:
    1. Send placeholder message immediately
    2. Update placeholder as processing progresses
    3. Replace with final response
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    log.info("telegram_processing_message", text=text[:100])

    # Handle /start command (instant response)
    if text == "/start":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Morning Briefing", callback_data="cmd:briefing"),
                InlineKeyboardButton("🐙 GitHub Digest", callback_data="cmd:github"),
            ],
            [
                InlineKeyboardButton("📈 Market Status", callback_data="cmd:markets"),
                InlineKeyboardButton("🔧 System Status", callback_data="cmd:status"),
            ]
        ])
        await telegram_service.send_message(WELCOME_MSG, reply_markup=keyboard)
        return

    # Send initial placeholder with progressive feedback
    placeholder_id = await telegram_service.send_message("🔍 Processing...")

    try:
        # Handle special commands
        if text.startswith("/briefing"):
            await telegram_service.edit_message(
                placeholder_id, "📊 Generating your morning briefing..."
            )
            from api.workers.briefing import send_morning_briefing
            await telegram_service.edit_message(placeholder_id, "✅ Briefing ready!")
            await send_morning_briefing({})
            # Delete placeholder after briefing is sent
            return

        if text.startswith("/markets"):
            await telegram_service.edit_message(
                placeholder_id, "📈 Fetching market data..."
            )
            from api.handlers import markets_handler
            async with async_session_factory() as db:
                await markets_handler.handle({}, db, update)
            await telegram_service.edit_message(placeholder_id, "✅ Market data ready!")
            return

        if text.startswith("/websearch"):
            query = text.replace("/websearch", "").strip()
            await telegram_service.edit_message(
                placeholder_id, f"🔎 Searching for: {query[:50]}..."
            )
            from api.handlers import websearch_handler
            async with async_session_factory() as db:
                await websearch_handler.handle({"query": query}, db, update)
            await telegram_service.edit_message(placeholder_id, "✅ Search complete!")
            return

        if text.startswith("/status"):
            await telegram_service.edit_message(
                placeholder_id, "🔧 Checking system status..."
            )
            async with async_session_factory() as db:
                try:
                    await dispatch(
                        IntentResult(intent="system_status", params={}), db, update
                    )
                    await db.commit()
                except Exception as exc:
                    log.error("status_command_error", error=str(exc))
                    await db.rollback()
            await telegram_service.edit_message(placeholder_id, "✅ Status check complete!")
            return

        # Check if user is in reply session
        async with async_session_factory() as db:
            try:
                result = await db.execute(
                    select(TelegramSession).where(
                        TelegramSession.user_id == settings.telegram_user_id
                    )
                )
                session = result.scalar_one_or_none()
                if session and session.state in ("awaiting_reply", "awaiting_approval"):
                    await telegram_service.edit_message(
                        placeholder_id, "💬 Processing your reply..."
                    )
                    await handle_reply({"text": text}, db, update)
                    await db.commit()
                    await telegram_service.edit_message(
                        placeholder_id, "✅ Reply sent!"
                    )
                    return
            except Exception as exc:
                log.error("session_check_error", error=str(exc))
                await db.rollback()

        # Get Redis for conversation history
        redis = await get_redis()
        
        # Get conversation history
        history = await get_history(redis)
        
        # Parse intent with progressive feedback
        await telegram_service.edit_message(placeholder_id, "🧠 Understanding your request...")
        
        async with async_session_factory() as db:
            try:
                # Check if this is first-time setup (no profile or no name)
                profile = await db.get(UserProfile, 1)
                if not profile:
                    profile = UserProfile(id=1)
                    db.add(profile)
                    await db.commit()
                    await db.refresh(profile)
                
                # First time user - ask for name
                if not profile.name and len(text.split()) <= 4:
                    profile.name = text.strip().split()[0].capitalize()
                    await db.commit()
                    response = f"Nice to meet you, {profile.name}! I'm ARIA, your personal AI assistant. Just talk to me naturally — I'll remember our conversations."
                    await telegram_service.edit_message(placeholder_id, response)
                    await append_turn(redis, "user", text)
                    await append_turn(redis, "assistant", response)
                    return
                
                # Build personalized system prompt with memories
                system_prompt = await build_system_prompt(
                    db, redis, query_text=text, task="conversation"
                )
                
                # Parse intent with context
                intent_result = await parse_intent_unified(text, history=history)
                intent = IntentResult(intent=intent_result.intent, params=intent_result.params)
                
                log.info(
                    "intent_parsed_with_context",
                    intent=intent.intent,
                    confidence=intent_result.confidence,
                    has_history=len(history) > 0,
                    params=str(intent.params)[:200]
                )

                # Update placeholder based on intent
                intent_messages = {
                    "reply": "💬 Preparing reply...",
                    "search": "🔍 Searching...",
                    "reminder": "⏰ Setting reminder...",
                    "expense": "💰 Recording expense...",
                    "note": "📝 Saving note...",
                    "github_action": "🐙 Accessing GitHub...",
                    "weather": "🌤 Fetching weather...",
                    "spotify": "🎵 Connecting to Spotify...",
                }
                
                progress_msg = intent_messages.get(intent.intent, "⚡ Processing...")
                await telegram_service.edit_message(placeholder_id, progress_msg)

                # If intent is "unknown", treat as general conversation
                if intent.intent == "unknown":
                    await telegram_service.edit_message(placeholder_id, "💭 Thinking...")
                    
                    # Use conversation history for context-aware response
                    response = await groq_client.chat_with_history(
                        system=system_prompt,
                        history=history,
                        current_message=text,
                        max_tokens=800,
                        temperature=0.75
                    )
                    
                    # Send response
                    await telegram_service.edit_message(placeholder_id, response)
                    
                    # Store conversation turn
                    await append_turn(redis, "user", text, intent="conversation")
                    await append_turn(redis, "assistant", response)
                    await maybe_compress(redis)
                    
                    # Extract memories in background (don't await)
                    try:
                        from api.llm.memory_extractor import extract_and_store
                        await extract_and_store(text, response, db)
                    except Exception as mem_exc:
                        log.warning("memory_extraction_failed", error=str(mem_exc))
                    
                    await db.commit()
                    return

                # Dispatch to handler for specific intents
                await dispatch(intent, db, update)
                await db.commit()
                
                # Store conversation turn for non-conversation intents too
                await append_turn(redis, "user", text, intent=intent.intent)
                await maybe_compress(redis)
                
                # Delete placeholder after successful dispatch
                try:
                    bot = telegram_service.get_bot()
                    await bot.delete_message(
                        chat_id=settings.telegram_user_id,
                        message_id=placeholder_id
                    )
                except Exception:
                    pass
                    
            except Exception as exc:
                log.error("dispatch_error", error=str(exc), intent=intent.intent if 'intent' in locals() else "unknown")
                await db.rollback()
                await telegram_service.edit_message(
                    placeholder_id,
                    "⚠️ Something went wrong processing your request."
                )

    except Exception as exc:
        log.error("message_processing_failed", error=str(exc))
        try:
            await telegram_service.edit_message(
                placeholder_id,
                "⚠️ An error occurred. Please try again."
            )
        except Exception:
            pass

# Made with Bob

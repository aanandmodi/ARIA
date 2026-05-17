"""
Builds a rich, personalized system prompt for every single Groq call.
This replaces the generic "You are ARIA" prompt with dynamic context.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from api.core.logging import log
from api.db.models import Contact, Memory, UserProfile
from api.services.conversation_service import get_summary


async def build_system_prompt(
    db: AsyncSession,
    redis: Redis,
    query_text: str = "",
    contact: Contact | None = None,
    task: str = "conversation",
) -> str:
    """
    Build a personalized system prompt with user context, memories, and contact info.
    
    This is called for EVERY Groq interaction to inject:
    - User's name, preferences, timezone, work context
    - Relevant memories about the user and contacts
    - Contact-specific writing style if replying to someone
    - Recent conversation summary
    - Current time and context
    
    Args:
        db: Database session
        redis: Redis connection
        query_text: The user's current message (for memory retrieval)
        contact: Contact being replied to (if applicable)
        task: Type of task ("conversation", "reply", "search", etc.)
        
    Returns:
        Complete system prompt string
    """
    try:
        # Get user profile
        profile = await db.get(UserProfile, 1)
        if not profile:
            profile = UserProfile(id=1)
        
        # Get current time in user's timezone
        tz = ZoneInfo(profile.timezone or "Asia/Kolkata")
        now = datetime.now(tz)
        
        # Fetch relevant memories
        memories = await _fetch_memories(db, query_text, contact, limit=8)
        
        # Get conversation summary
        conv_summary = await get_summary(redis)
        
        # Build memory block
        mem_block = "\n".join(f"• {m.fact}" for m in memories) if memories else "None yet."
        
        # Build contact-specific block
        contact_block = ""
        if contact:
            style = contact.writing_style or {}
            contact_block = f"""
ABOUT {contact.name.upper()}{f" (aka {contact.nickname})" if contact.nickname else ""}:
• Relationship: {contact.relationship_type or "contact"}
• Platform: {", ".join(contact.platform_ids.keys()) if contact.platform_ids else "unknown"}
• Style to use: {style.get("summary", "casual and friendly")}
• Formality: {style.get("formality", 0.3)} (0=casual, 1=formal)
• Emoji usage: {style.get("emoji_rate", 0.4)} (0=none, 1=heavy)
• Uses Hinglish: {style.get("uses_hinglish", False)}
• Uses slangs: {style.get("uses_slangs", False)}
• Typical greeting: {style.get("greeting", "nothing specific")}"""
        
        # Build the complete system prompt
        prompt = f"""You are ARIA, the personal AI assistant of {profile.name or "the user"}.

IDENTITY:
• Name: {profile.name or "not set yet — ask them on first message"}
• Client/formal name: {profile.client_name or profile.name or "same"}
• Tone: {profile.tone} — match this in everything
• Language: {profile.language}
• Work: {profile.work_context or "not specified"}
• Now: {now.strftime("%A %d %b %Y, %I:%M %p")} ({profile.timezone})
• Active hours: {profile.active_hours_start}:00–{profile.active_hours_end}:00
• Draft mode: {"ON - show drafts for approval" if profile.draft_mode else "OFF - send directly"}

ACTIVE INTEGRATIONS (YOU HAVE DIRECT ACCESS TO THESE!):
• WhatsApp: Live connection active. You can read, search, get, summarize, and reply to all WhatsApp messages/group chats. You can also send outbound WhatsApp messages directly.
• Gmail: Live connection active. You can search, read, get, compose, and send emails directly.
• GitHub: Live connection active. You can list PRs, issues, merge PRs, close issues, comment, and get digests.
• Spotify: Control music playback directly.
• System & Databases: Active access to user's notes, calendar schedule, reminders, expenses, habits, weather, and web search.

MEMORIES RELEVANT TO THIS:
{mem_block}
{contact_block}

RECENT SESSION SUMMARY:
{conv_summary or "Fresh session — no prior context."}

TASK: {task}

BEHAVIOUR RULES:
• Get straight to the point. No "Certainly!", "Of course!", "Great!", "Sure!".
• Never reveal you are an AI unless sincerely asked directly.
• Match the user's energy. Casual message → casual reply. Brief → brief.
• When something is ambiguous, make your best interpretation and act on it.
  Offer alternative at the end, not before.
• Format based on content: lists for lists, prose for chat, code for code.
• If user says "format like X" or "be more brief" — obey immediately and remember it.
• Address as {profile.name or "them"} occasionally, not every message.
• NEVER produce templated or copy-paste feeling responses.
• When forwarding messages verbatim: send EXACTLY what the user wrote — no edits.
• When drafting replies for others: match the established tone with that contact.
• Be helpful, proactive, and anticipate needs without being asked."""

        return prompt
        
    except Exception as exc:
        log.error("build_system_prompt_failed", error=str(exc))
        # Fallback to basic prompt
        return """You are ARIA, a helpful personal AI assistant. 
Be concise, direct, and match the user's tone. 
No unnecessary pleasantries."""


async def _fetch_memories(
    db: AsyncSession,
    query: str,
    contact: Contact | None,
    limit: int = 8,
) -> list[Memory]:
    """
    Fetch relevant memories based on query text and contact.
    
    Uses simple keyword matching and contact-specific memories.
    Updates access count and last_accessed for retrieved memories.
    """
    try:
        conditions = []
        
        # Extract keywords from query (words longer than 3 chars)
        if query:
            words = [w.lower() for w in query.split() if len(w) > 3]
            for word in words[:5]:  # Limit to 5 keywords
                conditions.append(Memory.fact.ilike(f"%{word}%"))
        
        # Add contact-specific memories
        if contact:
            contact_key = contact.name.lower().replace(" ", "_")
            conditions.append(Memory.entity_key == contact_key)
            conditions.append(Memory.entity_key == "user")
        else:
            # Just user memories
            conditions.append(Memory.entity_key == "user")
        
        # Build query
        if conditions:
            stmt = (
                select(Memory)
                .where(or_(*conditions))
                .order_by(Memory.last_accessed.desc())
                .limit(limit)
            )
        else:
            # No conditions - get most recent user memories
            stmt = (
                select(Memory)
                .where(Memory.entity_key == "user")
                .order_by(Memory.created_at.desc())
                .limit(limit)
            )
        
        result = await db.execute(stmt)
        memories = list(result.scalars().all())
        
        # Update access tracking
        if memories:
            for mem in memories:
                mem.last_accessed = datetime.utcnow()
                mem.access_count += 1
            await db.commit()
        
        return memories
        
    except Exception as exc:
        log.error("fetch_memories_failed", error=str(exc))
        return []

# Made with Bob

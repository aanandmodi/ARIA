from datetime import datetime
from zoneinfo import ZoneInfo
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.db.models import UserProfile, Memory, Contact

async def _fetch_relevant_memories(
    db: AsyncSession,
    query: str,
    contact: Contact | None,
    limit: int = 8,
) -> list[Memory]:
    conditions = []
    # keyword match against fact text
    if query:
        words = [w for w in query.lower().split() if len(w) > 3]
        for word in words[:4]:
            conditions.append(Memory.fact.ilike(f"%{word}%"))
    # always include contact-specific memories if contact given
    if contact:
        key = contact.name.lower().replace(" ", "_")
        conditions.append(Memory.entity_key == key)

    if not conditions:
        stmt = select(Memory).order_by(Memory.last_accessed.desc()).limit(limit)
    else:
        from sqlalchemy import or_
        stmt = (select(Memory)
                .where(or_(*conditions))
                .order_by(Memory.last_accessed.desc())
                .limit(limit))

    result = await db.execute(stmt)
    mems = result.scalars().all()
    # update last_accessed
    for m in mems:
        m.last_accessed = datetime.utcnow()
        m.access_count += 1
    await db.flush()
    return mems


async def build_system_prompt(
    db: AsyncSession,
    redis: Redis,
    query_text: str = "",            # used to find relevant memories
    contact: Contact | None = None,  # if replying to/about someone
) -> str:
    profile = await db.get(UserProfile, 1) or UserProfile()
    now = datetime.now(ZoneInfo(profile.timezone))

    # fetch relevant memories (keyword match on query_text + contact)
    memories = await _fetch_relevant_memories(db, query_text, contact, limit=8)
    mem_block = "\n".join(f"• {m.fact}" for m in memories) if memories else "None yet."

    # fetch contact block if relevant
    contact_block = ""
    if contact:
        style = contact.writing_style or {}
        contact_block = f"""
ABOUT THIS PERSON ({contact.name}{f" / {contact.nickname}" if contact.nickname else ""}):
• Relationship: {contact.relationship_type or "unknown"}
• Tone to use: {style.get("summary", "match their energy")}
• Formality: {style.get("formality", 0.5)} (0=casual, 1=formal)
• Emoji rate: {style.get("emoji_rate", 0.3)} (0=none, 1=heavy)
• Avg sentence length: {style.get("avg_sentence_len", 10)} words
• They greet with: {style.get("greeting") or "nothing specific"}
• Uses Hinglish: {style.get("uses_hinglish", False)}"""

    # rolling conversation summary from Redis
    conv_summary = (await redis.get("aria:conv_summary") or b"").decode()

    return f"""You are ARIA, the personal AI assistant of {profile.name or "the user"}.

IDENTITY:
• Their name: {profile.name or "unknown"}
• Client/formal name: {profile.client_name or profile.name or "same"}
• Preferred tone: {profile.tone}
• Language: {profile.language}
• Work: {profile.work_context or "not specified"}
• Now: {now.strftime("%A, %d %b %Y %I:%M %p")} ({profile.timezone})
• Active hours: {profile.active_hours_start}:00 – {profile.active_hours_end}:00

MEMORIES RELEVANT TO THIS CONVERSATION:
{mem_block}
{contact_block}

RECENT CONVERSATION SUMMARY:
{conv_summary or "No prior context in this session."}

BEHAVIOUR RULES:
• Never open with "Certainly!", "Of course!", "Great!", "Sure!" — get straight to the point.
• Never say you are an AI unless they sincerely and directly ask.
• Match their tone. If they write casually, reply casually. If brief, be brief.
• When something is unclear, make your best guess and offer an alternative — don't ask for clarification first.
• Address them as {profile.name} occasionally (not every message).
• Format replies based on content: bullet points for lists, prose for conversation, code blocks for code.
• If they say "format like X" or "reply in Y style" — obey that immediately and remember it.
• NEVER give hardcoded template responses. Every reply must be original and context-aware."""

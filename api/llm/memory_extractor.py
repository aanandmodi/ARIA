from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.db.models import Memory
from api.llm.client import chat_json
from api.core.logging import log

EXTRACT_PROMPT = """Read this exchange and extract facts worth remembering permanently.
Focus on: nicknames, personal details, preferences, relationship context,
recurring patterns, important dates/events.
Ignore: one-time task completions, generic pleasantries.

Return ONLY a JSON object with a "facts" key containing an array (empty [] if nothing new):
{{
  "facts": [
    {{
      "entity_type": "contact_nickname|user_fact|preference|contact_context|user_routine",
      "entity_key": "snake_case_contact_name or 'user'",
      "fact": "concise plain English statement",
      "confidence": 0.0-1.0
    }}
  ]
}}

User: "{user_msg}"
ARIA: "{aria_reply}"
"""

EXTRACT_SYSTEM = "Extract memorable facts from the exchange. Return ONLY a JSON object with a 'facts' array."


async def extract_and_store(user_msg: str, aria_reply: str, db: AsyncSession):
    """Extract facts from an exchange and store new ones as Memory rows."""
    try:
        raw = await chat_json(
            EXTRACT_PROMPT.format(user_msg=user_msg, aria_reply=aria_reply),
            system=EXTRACT_SYSTEM,
        )
        items = raw.get("facts", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
        for item in items:
            if not isinstance(item, dict) or not item.get("fact"):
                continue
            exists = await db.scalar(
                select(Memory).where(
                    Memory.entity_key == item.get("entity_key", "user"),
                    Memory.fact.ilike(f"%{item.get('fact','')[:25]}%"),
                )
            )
            if not exists:
                db.add(Memory(
                    entity_type=item.get("entity_type", "user_fact"),
                    entity_key=item.get("entity_key", "user"),
                    fact=item.get("fact", ""),
                    confidence=float(item.get("confidence", 0.9)),
                    source="inferred",
                ))
        await db.flush()
    except Exception as exc:
        log.error("memory_extraction_failed", error=str(exc))


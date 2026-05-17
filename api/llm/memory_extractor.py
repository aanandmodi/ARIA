"""
After every ARIA conversation turn, extract new facts to remember.
This runs in the background and doesn't block the main conversation flow.
"""
from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.logging import log
from api.db.models import Contact, Memory
from api.llm.client import groq_client

EXTRACT_PROMPT = """Read this conversation exchange and extract any facts worth remembering permanently.
Focus on: nicknames, personal details, preferences, relationship context, recurring patterns.
Ignore: one-time tasks, generic pleasantries, things already obvious.

Return ONLY a JSON array ([] if nothing new):
[
  {{
    "entity_type": "contact_nickname|contact_style|user_fact|preference|contact_context|user_routine",
    "entity_key": "snake_case_name_or_user",
    "fact": "concise plain English statement",
    "confidence": 0.0-1.0
  }}
]

User said: "{user_msg}"
ARIA replied: "{aria_reply}" """


async def extract_and_store(
    user_msg: str,
    aria_reply: str,
    db: AsyncSession,
) -> None:
    """
    Extract memorable facts from a conversation exchange and store them.
    
    This is called after every conversation turn but doesn't block the response.
    Failures are logged but don't affect the user experience.
    """
    try:
        # Ask Groq to extract facts
        raw = await groq_client.chat_json(
            EXTRACT_PROMPT.format(
                user_msg=user_msg[:500],
                aria_reply=aria_reply[:500]
            ),
            system="Extract memorable facts. Return ONLY a JSON array. If nothing, return []",
        )
        
        facts = raw if isinstance(raw, list) else []
        
        for item in facts:
            if not item.get("fact") or not item.get("entity_key"):
                continue
                
            # Check if similar memory already exists
            exists = await db.scalar(
                select(Memory).where(
                    Memory.entity_key == item["entity_key"],
                    Memory.fact.ilike(f"%{item['fact'][:30]}%"),
                )
            )
            
            if not exists:
                memory = Memory(
                    entity_type=item.get("entity_type", "user_fact"),
                    entity_key=item.get("entity_key", "user"),
                    fact=item["fact"],
                    confidence=float(item.get("confidence", 0.85)),
                    source="inferred",
                )
                db.add(memory)
                log.info("memory_extracted", 
                        entity=memory.entity_key, 
                        fact=memory.fact[:50])
        
        if facts:
            await db.commit()
            
    except Exception as exc:
        log.warning("memory_extraction_failed", error=str(exc))
        # Don't raise - memory extraction is best-effort


async def detect_pet_name(
    message: str,
    contact: Contact,
    db: AsyncSession,
) -> None:
    """
    Detect if the user referred to a contact by a nickname/pet name.
    Updates the contact's nickname field if found.
    """
    try:
        PET_NAME_PROMPT = """Did the user refer to "{official_name}" by a nickname or pet name?
Return ONLY JSON: {{"found": true/false, "nickname": "string or null"}}
User's message: "{message}" """
        
        result = await groq_client.chat_json(
            PET_NAME_PROMPT.format(
                official_name=contact.name,
                message=message[:300]
            ),
            system="Detect nickname. Return only JSON.",
        )
        
        if result.get("found") and result.get("nickname"):
            nickname = result["nickname"]
            if nickname.lower() != (contact.nickname or "").lower():
                contact.nickname = nickname
                db.add(Memory(
                    entity_type="contact_nickname",
                    entity_key=contact.name.lower().replace(" ", "_"),
                    fact=f"goes by '{nickname}'",
                    source="inferred",
                    confidence=0.95,
                ))
                await db.commit()
                log.info("pet_name_detected", 
                        contact=contact.name, 
                        nickname=nickname)
                
    except Exception as exc:
        log.warning("pet_name_detection_failed", error=str(exc))

# Made with Bob

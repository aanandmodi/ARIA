"""
Message classification via Groq LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from api.core.logging import log
from api.llm.client import chat_json
from api.llm.prompts import CLASSIFY_PROMPT, CLASSIFY_SYSTEM


@dataclass
class ClassifyResult:
    importance: int
    category: str
    summary: str
    needs_reply: bool
    urgency: str


async def classify(
    platform: str,
    sender_id: str,
    sender_name: str,
    content: str,
) -> ClassifyResult:
    """
    Classify an inbound message using Groq.
    Returns a safe default on any error.
    """
    try:
        prompt = CLASSIFY_PROMPT.format(
            platform=platform,
            sender_id=sender_id,
            sender_name=sender_name or "Unknown",
            content=content[:3000],  # truncate very long messages
        )
        data = await chat_json(prompt, system=CLASSIFY_SYSTEM, max_tokens=256)

        return ClassifyResult(
            importance=int(data.get("importance", 5)),
            category=str(data.get("category", "unknown")),
            summary=str(data.get("summary", content[:80])),
            needs_reply=bool(data.get("needs_reply", False)),
            urgency=str(data.get("urgency", "whenever")),
        )
    except Exception as exc:
        log.error("classify_failed", error=str(exc), platform=platform, sender=sender_id)
        return ClassifyResult(
            importance=5,
            category="unknown",
            summary=content[:80] if content else "Empty message",
            needs_reply=False,
            urgency="whenever",
        )

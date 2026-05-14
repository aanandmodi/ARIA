"""
User intent parsing via Groq LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from api.core.config import settings
from api.core.logging import log
from api.llm.client import chat_json
from api.llm.prompts import INTENT_PROMPT, INTENT_SYSTEM

KNOWN_INTENTS = {
    "reply", "reminder", "search", "schedule", "note", "expense",
    "habit", "spotify", "weather", "summary", "github_action", "unknown",
    "briefing", "markets", "websearch", "create_memory", "send_sms", "system_status", "compose_email"
}


@dataclass
class IntentResult:
    intent: str
    params: dict = field(default_factory=dict)


async def parse_intent(message: str) -> IntentResult:
    """
    Parse user's Telegram message into a structured intent.
    Falls back to 'unknown' on error.
    """
    try:
        tz = ZoneInfo(settings.timezone)
        today = datetime.now(tz).isoformat()

        prompt = INTENT_PROMPT.format(today=today, message=message[:2000])
        data = await chat_json(prompt, system=INTENT_SYSTEM, max_tokens=512)

        intent = str(data.get("intent", "unknown")).lower()
        if intent not in KNOWN_INTENTS:
            intent = "unknown"

        params = data.get("params", {})
        if not isinstance(params, dict):
            params = {}

        return IntentResult(intent=intent, params=params)

    except Exception as exc:
        log.error("intent_parse_failed", error=str(exc), message=message[:100])
        return IntentResult(intent="unknown", params={})

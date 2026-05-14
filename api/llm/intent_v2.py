"""
Advanced User intent parsing via Groq LLM (V2).
Supports robust JSON structured output for deep integrations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional

from api.core.config import settings
from api.core.logging import log
from api.llm.client import chat_json

KNOWN_INTENTS_V2 = {
    "chat", 
    "create_event", 
    "read_email", 
    "github_action", 
    "create_memory", 
    "send_sms", 
    "system_status",
    "unknown"
}

INTENT_V2_SYSTEM = """You are ARIA's advanced natural language understanding core.
Your job is to analyze the user's message and extract their underlying intent.
Always respond in JSON format.

Supported intents:
- chat: A normal conversation, question, or statement.
- create_event: Wants to schedule something or create a reminder.
- read_email: Wants to check or read emails.
- github_action: Wants to perform a GitHub action (e.g., check PRs, run workflows).
- create_memory: Explicitly telling you to remember a fact or preference.
- send_sms: Wants to send an SMS message.
- system_status: Wants to check your status, database, or workers.
- unknown: Cannot determine the intent.

JSON Schema:
{
    "primary_intent": "one of the supported intents",
    "confidence": 0.95,
    "parameters": {
        "key": "extracted values specific to the intent"
    }
}
"""

INTENT_V2_PROMPT = """Current Time: {today}
User Message: {message}

Extract the intent and parameters as JSON.
"""

@dataclass
class IntentResultV2:
    intent: str
    confidence: float
    params: Dict[str, Any] = field(default_factory=dict)


async def parse_intent_v2(message: str) -> IntentResultV2:
    """
    Parse user's Telegram message into a structured intent using V2 logic.
    Falls back to 'chat' or 'unknown' on error.
    """
    try:
        tz = ZoneInfo(settings.timezone)
        today = datetime.now(tz).isoformat()

        prompt = INTENT_V2_PROMPT.format(today=today, message=message[:2000])
        data = await chat_json(prompt, system=INTENT_V2_SYSTEM, max_tokens=512)

        intent = str(data.get("primary_intent", "unknown")).lower()
        if intent not in KNOWN_INTENTS_V2:
            intent = "chat"  # Default to chat instead of unknown for more natural interaction

        confidence = float(data.get("confidence", 0.0))
        
        params = data.get("parameters", {})
        if not isinstance(params, dict):
            params = {}

        return IntentResultV2(intent=intent, confidence=confidence, params=params)

    except Exception as exc:
        log.error("intent_parse_v2_failed", error=str(exc), message=message[:100])
        return IntentResultV2(intent="chat", confidence=0.0, params={})

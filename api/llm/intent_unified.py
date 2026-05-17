"""
Unified intent parser - Single-tier, hyper-optimized LLM intent extraction.
Uses fast model (llama-3.1-8b-instant) for all intent parsing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from api.core.config import settings
from api.core.logging import log
from api.llm.client import chat_json

# All supported intents in one unified system
UNIFIED_INTENTS = {
    "reply", "compose_email", "reminder", "search", "schedule", "note", 
    "expense", "habit", "spotify", "weather", "summary", "github_action",
    "create_memory", "send_sms", "system_status", "briefing", "markets",
    "websearch", "send_whatsapp", "list_contacts", "unknown"
}

UNIFIED_INTENT_SYSTEM = """You are ARIA's natural language understanding engine.
Analyze the user's message and extract their intent with high precision.

SUPPORTED INTENTS:
- reply: Reply to an email, WhatsApp, or other message
- compose_email: Compose a new email
- reminder: Set a reminder or alarm
- search: Search emails, messages, or notes (use this when the user is searching for a specific topic, keyword, or person on WhatsApp/Gmail/etc.)
- schedule: View or manage calendar
- note: Create or retrieve a note
- expense: Track an expense or spending
- habit: Log a habit or track progress
- spotify: Control Spotify playback
- weather: Get weather forecast
- summary: Summarize messages or content (use this when the user asks to check, read, get, or summarize recent/unread messages or notifications from any platform like WhatsApp, Gmail, etc. E.g., "any whatsapp messages?", "check my messages", "summarize my emails")
- github_action: GitHub operations (PRs, issues, commits, etc.)
- create_memory: Remember a fact or preference
- send_sms: Send an SMS message
- send_whatsapp: Send a WhatsApp message
- list_contacts: List contacts from WhatsApp/Gmail
- system_status: Check system health
- briefing: Get morning briefing
- markets: Check stocks/crypto prices
- websearch: Search the web
- unknown: General conversation or unclear intent

PARAMETER EXTRACTION RULES:
1. For "reply": extract message_id if mentioned, otherwise null
2. For "compose_email": extract to, subject, body
3. For "reminder": extract time (ISO format), description
4. For "search": extract query, platform (email/whatsapp/all)
5. For "expense": extract amount, category, description
6. For "github_action": extract action (prs/issues/merge/close/comment/create_issue/commit), repo, number, text
7. For "send_whatsapp": extract contact_name or phone, message
8. For "list_contacts": extract platform (whatsapp/gmail/all)
9. For "create_memory": extract fact, entity (person/place/preference)
10. For "summary": extract platform (gmail/whatsapp/all), period (today/week/month/all)

CONTEXT AWARENESS:
- Detect if message refers to a group or personal chat
- Extract contact names mentioned in the message
- Identify urgency level (urgent/normal/low)

Always respond in valid JSON format.

JSON Schema:
{
    "intent": "one of the supported intents",
    "confidence": 0.95,
    "params": {
        "key": "extracted values"
    },
    "context": {
        "is_group": false,
        "mentioned_contacts": [],
        "urgency": "normal"
    }
}
"""

UNIFIED_INTENT_PROMPT = """Current Time: {today}
User Timezone: {timezone}

CONVERSATION HISTORY:
{history_context}

User Message: {message}

Extract the intent, parameters, and context as JSON.
Be precise and confident in your classification.
"""


@dataclass
class UnifiedIntentResult:
    intent: str
    confidence: float
    params: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)


async def parse_intent_unified(message: str, history: list[dict] | None = None) -> UnifiedIntentResult:
    """
    Parse user intent using a single, optimized LLM call.
    
    Uses llama-3.1-8b-instant for speed (<500ms response time).
    Falls back to 'unknown' for general conversation.
    """
    try:
        tz = ZoneInfo(settings.timezone)
        today = datetime.now(tz).isoformat()

        history_context = "No previous history."
        if history:
            # Take last 6 entries (3 turns)
            recent = history[-6:]
            turns = []
            for turn in recent:
                role = "User" if turn.get("role") == "user" else "Assistant"
                content = turn.get("content", "")
                turns.append(f"{role}: {content}")
            if turns:
                history_context = "\n".join(turns)

        prompt = UNIFIED_INTENT_PROMPT.format(
            today=today,
            timezone=settings.timezone,
            history_context=history_context,
            message=message[:2000]
        )
        
        # Use fast model for intent parsing
        data = await chat_json(
            prompt, 
            system=UNIFIED_INTENT_SYSTEM,
            model="llama-3.1-8b-instant",  # Fast model
            max_tokens=512,
            temperature=0.1  # Low temperature for consistent parsing
        )

        intent = str(data.get("intent", "unknown")).lower()
        if intent not in UNIFIED_INTENTS:
            intent = "unknown"

        confidence = float(data.get("confidence", 0.0))
        params = data.get("params", {})
        context = data.get("context", {})
        
        if not isinstance(params, dict):
            params = {}
        if not isinstance(context, dict):
            context = {}

        log.info(
            "intent_unified_parsed",
            intent=intent,
            confidence=confidence,
            has_context=bool(context)
        )

        return UnifiedIntentResult(
            intent=intent,
            confidence=confidence,
            params=params,
            context=context
        )

    except Exception as exc:
        log.error("intent_unified_parse_failed", error=str(exc), message=message[:100])
        return UnifiedIntentResult(
            intent="unknown",
            confidence=0.0,
            params={},
            context={}
        )

# Made with Bob

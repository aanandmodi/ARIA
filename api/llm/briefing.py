"""
Morning briefing composition via Groq.
"""

from __future__ import annotations

from api.core.logging import log
from api.llm.client import chat
from api.llm.prompts import BRIEFING_PROMPT, BRIEFING_SYSTEM


async def compose_briefing(
    weather: str = "No data",
    events: str = "No events",
    emails: str = "No urgent emails",
    whatsapp: str = "No unread messages",
    reminders: str = "No pending reminders",
    markets: str = "No market data",
    hn: str = "No stories",
    github: str = "No updates",
) -> str:
    """
    Compose a formatted morning briefing from aggregated data sections.
    """
    try:
        prompt = BRIEFING_PROMPT.format(
            weather=weather,
            events=events,
            emails=emails,
            whatsapp=whatsapp,
            reminders=reminders,
            markets=markets,
            hn=hn,
            github=github,
        )
        result = await chat(prompt, system=BRIEFING_SYSTEM, max_tokens=1500)
        return result.strip() if result.strip() else "☀️ Good morning! No briefing data available today."
    except Exception as exc:
        log.error("briefing_compose_failed", error=str(exc))
        return "☀️ Good morning! Briefing generation failed — check logs for details."

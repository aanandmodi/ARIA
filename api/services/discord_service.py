"""
Discord service — send messages via discord.py REST.
"""

from __future__ import annotations

import httpx

from api.core.config import settings
from api.core.logging import log

DISCORD_API_BASE = "https://discord.com/api/v10"


async def send_message(channel_id: str, text: str) -> bool:
    """Send a text message to a Discord channel."""
    if not settings.discord_bot_token:
        log.warning("discord_not_configured")
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {settings.discord_bot_token}",
                    "Content-Type": "application/json",
                },
                json={"content": text},
            )
            resp.raise_for_status()
            log.info("discord_sent", channel_id=channel_id, length=len(text))
            return True
    except Exception as exc:
        log.error("discord_send_failed", error=str(exc), channel_id=channel_id)
        return False

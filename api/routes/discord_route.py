"""
Discord webhook route (for external integrations; main bot runs via discord.py).
"""
from __future__ import annotations
from fastapi import APIRouter, Request, Response
from api.core.logging import log

router = APIRouter()

@router.post("/discord")
async def discord_webhook(request: Request) -> Response:
    """Placeholder for Discord webhook integrations. Main bot uses discord.py gateway."""
    try:
        body = await request.json()
        log.info("discord_webhook_received", keys=list(body.keys()))
        return Response(status_code=200)
    except Exception as exc:
        log.error("discord_webhook_error", error=str(exc))
        return Response(status_code=200)

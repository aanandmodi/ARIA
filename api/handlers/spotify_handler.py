"""
Spotify handler — music commands.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, spotify_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    action = params.get("action", "nowplaying")
    query = params.get("query")
    if action == "play":
        r = await spotify_service.play(query)
    elif action == "pause":
        r = await spotify_service.pause()
    elif action == "skip":
        r = await spotify_service.skip()
    elif action == "queue" and query:
        r = await spotify_service.queue_track(query)
    else:
        r = await spotify_service.now_playing()
    await telegram_service.send_message(r)

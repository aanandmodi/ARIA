"""
Schedule handler — create calendar events, find free slots.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, calendar_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle schedule intent."""
    contact = params.get("contact", "")
    when = params.get("when", "")
    event_type = params.get("type", "meeting")
    if not when:
        await telegram_service.send_message("📅 When should I schedule this?")
        return
    summary = f"{event_type.capitalize()} with {contact}" if contact else event_type.capitalize()
    event_id = await calendar_service.create_event(summary=summary, start_time=when, attendees=[contact] if "@" in (contact or "") else None)
    if event_id:
        await telegram_service.send_message(f"📅 <b>Event created!</b>\n\n📌 {summary}\n🕐 {when}")
    else:
        await telegram_service.send_message("❌ Could not create calendar event. Is Google Calendar configured?")

"""
Reminder handler — create, list, delete reminders.
"""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.core.config import settings
from api.core.logging import log
from api.db.models import Reminder
from api.services import telegram_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle reminder intent."""
    when_str = params.get("when", "")
    about = params.get("about", "Reminder")
    try:
        tz = ZoneInfo(settings.timezone)
        if when_str:
            fire_at = datetime.fromisoformat(when_str.replace("Z", "+00:00"))
        else:
            fire_at = datetime.now(tz)

        reminder = Reminder(fire_at=fire_at, message=about, status="pending")
        db.add(reminder)
        await db.flush()

        time_str = fire_at.strftime("%b %d, %Y at %I:%M %p")
        await telegram_service.send_message(f"⏰ <b>Reminder set!</b>\n\n📌 {about}\n🕐 {time_str}")
        log.info("reminder_created", about=about, fire_at=fire_at.isoformat())
    except Exception as exc:
        log.error("reminder_failed", error=str(exc))
        await telegram_service.send_message("❌ Could not create reminder. Check the date format.")

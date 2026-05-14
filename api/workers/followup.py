"""
Follow-up nudge worker.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select
from api.core.config import settings
from api.core.logging import log
from api.db.models import Message
from api.db.session import get_db_session
from api.services import telegram_service

async def check_followup_nudges(ctx: dict) -> None:
    """Check for messages needing reply that haven't been replied to."""
    async with get_db_session() as db:
        cutoff = datetime.utcnow() - timedelta(days=settings.follow_up_days)
        stmt = select(Message).where(
            Message.needs_reply == True,
            Message.replied_at.is_(None),
            Message.silenced == False,
            Message.created_at <= cutoff,
        ).order_by(Message.created_at.desc()).limit(10)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        if messages:
            lines = ["⏰ <b>Follow-up Reminders</b>\n\nThese messages need your reply:\n"]
            for m in messages:
                emoji = telegram_service.PLATFORM_EMOJI.get(m.platform, "📨")
                days_ago = (datetime.utcnow() - m.created_at).days
                lines.append(f"{emoji} <b>{m.sender_name}</b> ({days_ago}d ago)\n   {m.summary or m.content[:80]}")
            await telegram_service.send_message("\n".join(lines))
            log.info("followup_nudges_sent", count=len(messages))

async def check_single_followup(ctx: dict, msg_id: str) -> None:
    """Check if a specific message still needs a reply."""
    async with get_db_session() as db:
        from uuid import UUID
        result = await db.execute(select(Message).where(Message.id == UUID(msg_id)))
        msg = result.scalar_one_or_none()
        if msg and msg.needs_reply and not msg.replied_at and not msg.silenced:
            emoji = telegram_service.PLATFORM_EMOJI.get(msg.platform, "📨")
            await telegram_service.send_message(
                f"⏰ <b>Follow-up reminder</b>\n\n"
                f"{emoji} <b>{msg.sender_name}</b> is waiting for your reply:\n"
                f"{msg.summary or msg.content[:100]}"
            )

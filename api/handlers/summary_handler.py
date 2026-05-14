"""
Summary handler — on-demand summaries of any platform.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.db.models import Message
from api.llm.summarise import summarise
from api.services import telegram_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    platform = params.get("platform", "all")
    period = params.get("period", "today")
    if period == "today":
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0)
    elif period == "week":
        cutoff = datetime.utcnow() - timedelta(days=7)
    elif period == "month":
        cutoff = datetime.utcnow() - timedelta(days=30)
    elif period == "all":
        cutoff = datetime.min
    else: # unread or default
        cutoff = datetime.utcnow() - timedelta(days=1)
    stmt = select(Message).where(Message.created_at >= cutoff).order_by(Message.created_at.desc()).limit(50)
    if platform != "all":
        stmt = stmt.where(Message.platform == platform)
    result = await db.execute(stmt)
    messages = result.scalars().all()
    if not messages:
        await telegram_service.send_message(f"📊 No messages found for {platform} ({period}).")
        return
    combined = "\n".join([f"[{m.platform}] {m.sender_name}: {m.summary or m.content[:100]}" for m in messages[:30]])
    summary = await summarise(combined, context_type=f"{platform} {period} messages")
    emoji = telegram_service.PLATFORM_EMOJI.get(platform, "📊")
    await telegram_service.send_message(f"{emoji} <b>Summary ({platform}, {period})</b>\n\n{summary}")

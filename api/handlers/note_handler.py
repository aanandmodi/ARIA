"""
Note handler — create and search notes.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.db.models import Note
from api.services import telegram_service, notion_service
from api.core.logging import log

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle note intent."""
    content = params.get("content", "")
    title = params.get("title", "Quick Note")
    url = params.get("url")
    if not content:
        await telegram_service.send_message("📝 What would you like to note down?")
        return
    # Save to DB
    note = Note(title=title, content=content, source_url=url, tags=[])
    db.add(note)
    await db.flush()
    # Also save to Notion if configured
    notion_id = await notion_service.create_note(title, content, source_url=url, tags=[])
    if notion_id:
        note.notion_id = notion_id
        await db.flush()
    await telegram_service.send_message(f"📝 <b>Note saved!</b>\n\n📌 {title}\n{content[:200]}")
    log.info("note_created", title=title, notion_id=notion_id)

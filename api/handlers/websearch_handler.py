"""
Websearch handler — search the internet using DuckDuckGo.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service
from duckduckgo_search import DDGS
from api.core.logging import log

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle websearch intent."""
    query = params.get("query", "")
    if not query:
        await telegram_service.send_message("🔍 What would you like me to search the web for?")
        return

    await telegram_service.send_typing()
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            await telegram_service.send_message(f"🔍 No web results found for: <i>{query}</i>")
            return
            
        lines = [f"🔍 <b>Web Search:</b> <i>{query}</i>\n"]
        for i, r in enumerate(results):
            lines.append(f"<b>{i+1}. <a href='{r.get('href', '')}'>{r.get('title', 'No title')}</a></b>")
            lines.append(f"{r.get('body', '')}\n")
            
        await telegram_service.send_message("\n".join(lines))
    except Exception as exc:
        log.error("websearch_error", error=str(exc))
        await telegram_service.send_message("❌ Web search failed.")

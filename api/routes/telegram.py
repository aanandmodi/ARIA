"""
Telegram webhook route — the primary user interface.
"""
from __future__ import annotations
import json
from fastapi import APIRouter, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.core.config import settings
from api.core.logging import log
from api.db.models import TelegramSession
from api.db.session import async_session_factory
from api.llm.intent import parse_intent
from api.handlers.router import dispatch
from api.handlers.reply_handler import handle_callback, handle as handle_reply
from api.services import telegram_service

router = APIRouter()

WELCOME_MSG = (
    "👋 <b>Welcome to ARIA!</b>\n\n"
    "I'm your personal AI assistant. I'll notify you about important messages "
    "from Gmail, WhatsApp, Discord, Slack, and more.\n\n"
    "Just type naturally — I understand commands like:\n"
    "• <i>remind me about X tomorrow 9am</i>\n"
    "• <i>search emails about project</i>\n"
    "• <i>spent 500 on dinner</i>\n"
    "• <i>play some jazz</i>\n\n"
    "🚀 ARIA is online and ready!"
)

@router.post("/telegram")
async def telegram_webhook(request: Request) -> Response:
    """Handle inbound Telegram webhook updates."""
    # 1. Verify secret token
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.telegram_webhook_secret and secret != settings.telegram_webhook_secret:
        log.warning("telegram_webhook_invalid_secret")
        return Response(status_code=403)

    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    # 2. Parse Update
    try:
        update = Update.de_json(body, telegram_service.get_bot())
    except Exception as exc:
        log.error("telegram_update_parse_failed", error=str(exc))
        return Response(status_code=200)

    if update is None:
        return Response(status_code=200)

    # 3. Handle callback queries (inline button presses)
    if update.callback_query:
        user_id = update.callback_query.from_user.id if update.callback_query.from_user else 0
        if user_id != settings.telegram_user_id:
            return Response(status_code=200)
        async with async_session_factory() as db:
            try:
                await handle_callback(update.callback_query, db)
                await db.commit()
            except Exception as exc:
                log.error("callback_handler_error", error=str(exc))
                await db.rollback()
        return Response(status_code=200)

    # 4. Handle text messages
    if not update.message or not update.message.text:
        return Response(status_code=200)

    from_user = update.message.from_user
    if not from_user or from_user.id != settings.telegram_user_id:
        log.warning("telegram_unauthorized_user", user_id=from_user.id if from_user else 0)
        return Response(status_code=200)

    text = update.message.text.strip()
    log.info("telegram_message_received", text=text[:100])

    # Handle /start command
    if text == "/start":
        await telegram_service.send_message(WELCOME_MSG)
        return Response(status_code=200)

    if text.startswith("/briefing"):
        await telegram_service.send_typing()
        from api.workers.briefing import send_morning_briefing
        await send_morning_briefing({})
        return Response(status_code=200)

    if text.startswith("/markets"):
        await telegram_service.send_typing()
        from api.handlers import markets_handler
        async with async_session_factory() as db:
            await markets_handler.handle({}, db, update)
        return Response(status_code=200)

    if text.startswith("/websearch"):
        await telegram_service.send_typing()
        query = text.replace("/websearch", "").strip()
        from api.handlers import websearch_handler
        async with async_session_factory() as db:
            await websearch_handler.handle({"query": query}, db, update)
        return Response(status_code=200)

    # 4b. Check if user is in reply session — if so, bypass LLM intent
    #     and route directly to reply handler
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(TelegramSession).where(
                    TelegramSession.user_id == settings.telegram_user_id
                )
            )
            session = result.scalar_one_or_none()
            if session and session.state in ("awaiting_reply", "awaiting_approval"):
                await telegram_service.send_typing()
                await handle_reply({"text": text}, db, update)
                await db.commit()
                return Response(status_code=200)
        except Exception as exc:
            log.error("session_check_error", error=str(exc))
            await db.rollback()

    # 5. Parse intent via LLM
    await telegram_service.send_typing()
    intent = await parse_intent(text)
    log.info("intent_parsed", intent=intent.intent, params=str(intent.params)[:200])

    # 6. Dispatch to handler
    async with async_session_factory() as db:
        try:
            await dispatch(intent, db, update)
            await db.commit()
        except Exception as exc:
            log.error("dispatch_error", error=str(exc), intent=intent.intent)
            await db.rollback()
            await telegram_service.send_message("⚠️ Something went wrong processing your request.")

    return Response(status_code=200)

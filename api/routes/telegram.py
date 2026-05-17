"""
Telegram webhook route — Ultra-fast webhook with ARQ offloading.
Zero-timeout architecture: acknowledge within 50ms, process asynchronously.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from telegram import Update

from api.core.config import settings
from api.core.logging import log
from api.core.queue import enqueue
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
    "• <i>play some jazz</i>\n"
    "• <i>check my github PRs</i>\n"
    "• <i>remember that John prefers email</i>\n"
    "• <i>send sms to +91... saying ...</i>\n"
    "• <i>system status</i>\n\n"
    "🚀 ARIA is online and ready!"
)

@router.post("/telegram")
async def telegram_webhook(request: Request) -> Response:
    """
    Handle inbound Telegram webhook updates.
    
    ZERO-TIMEOUT ARCHITECTURE:
    - Verify secret token (5ms)
    - Parse update (10ms)
    - Enqueue to ARQ worker (20ms)
    - Return 200 OK (total: <50ms)
    
    All processing happens asynchronously in the worker.
    """
    # 1. Verify secret token (fast path)
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.telegram_webhook_secret and secret != settings.telegram_webhook_secret:
        log.warning("telegram_webhook_invalid_secret")
        return Response(status_code=403)

    # 2. Parse raw body
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=400)

    # 3. Quick validation - parse Update
    try:
        update = Update.de_json(body, telegram_service.get_bot())
    except Exception as exc:
        log.error("telegram_update_parse_failed", error=str(exc))
        return Response(status_code=200)

    if update is None:
        return Response(status_code=200)

    # 4. Extract user ID for authorization
    user_id = None
    if update.callback_query and update.callback_query.from_user:
        user_id = update.callback_query.from_user.id
    elif update.message and update.message.from_user:
        user_id = update.message.from_user.id

    # 5. Quick auth check
    if user_id and user_id != settings.telegram_user_id:
        log.warning("telegram_unauthorized_user", user_id=user_id)
        return Response(status_code=200)

    # 6. Enqueue to ARQ worker for async processing
    # Convert Update to dict for serialization
    await enqueue("process_telegram_update", body)
    
    log.info("telegram_update_enqueued",
             has_message=bool(update.message),
             has_callback=bool(update.callback_query))

    # 7. Return immediately - worker handles everything else
    return Response(status_code=200)


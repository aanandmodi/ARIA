"""
ARIA FastAPI application factory with lifespan management.
"""
from __future__ import annotations
import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.core.config import settings
from api.core.logging import log
from api.core.queue import close_pools
from api.core.storage import ensure_bucket
from api.db.models import Base
from api.db.session import engine

_discord_task = None


def _validate_required_settings():
    """Check that essential config values are set."""
    missing = []
    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.telegram_user_id:
        missing.append("TELEGRAM_USER_ID")
    if not settings.groq_api_key:
        missing.append("GROQ_API_KEY")
    if missing:
        print(f"\n❌ Missing required settings: {', '.join(missing)}")
        print("   Run: python aria_setup.py")
        print("   Or add them to your .env file.\n")
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _discord_task
    _validate_required_settings()

    # 1. Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_tables_created")

    # 2. Create MinIO bucket
    try:
        await ensure_bucket()
    except Exception as exc:
        log.warning("minio_bucket_init_failed", error=str(exc))

    # 3. Redis pool is lazy-init'd on first use

    # 4. Start Discord bot if configured
    if settings.discord_bot_token:
        from api.discord_bot.bot import start_bot
        _discord_task = asyncio.create_task(start_bot())
        log.info("discord_bot_task_started")

    # 5. Register Telegram webhook
    try:
        from api.services.telegram_service import get_bot
        from telegram import BotCommand
        bot = get_bot()
        await bot.set_my_commands([
            BotCommand("start", "Start or restart ARIA"),
            BotCommand("search", "Search emails, WhatsApp, notes"),
            BotCommand("remind", "Set a reminder"),
            BotCommand("summary", "Get a summary of messages"),
            BotCommand("weather", "Check weather forecast"),
            BotCommand("briefing", "Get your morning briefing"),
            BotCommand("markets", "Check stock & crypto prices"),
            BotCommand("websearch", "Search the internet"),
            BotCommand("status", "System health & stats"),
        ])
        log.info("telegram_bot_initialized_with_commands")
    except Exception as exc:
        log.warning("telegram_bot_init_failed", error=str(exc))

    # 6. Setup Gmail watch if configured
    if settings.gmail_refresh_token:
        try:
            from api.services.gmail_service import setup_pubsub_watch
            await setup_pubsub_watch()
        except Exception as exc:
            log.warning("gmail_watch_init_failed", error=str(exc))

    log.info("aria_backend_started", version="1.0.0")
    yield

    # SHUTDOWN
    if _discord_task and not _discord_task.done():
        _discord_task.cancel()
        try:
            await _discord_task
        except asyncio.CancelledError:
            pass
    await close_pools()
    await engine.dispose()
    log.info("aria_backend_stopped")


app = FastAPI(title="ARIA", version="1.0.0", lifespan=lifespan)

# Include routers
from api.routes.telegram import router as telegram_router
from api.routes.gmail import router as gmail_router
from api.routes.slack import router as slack_router
from api.routes.discord_route import router as discord_route_router
from api.routes.internal import router as internal_router
from api.routes.sms import router as sms_router

app.include_router(telegram_router, prefix="/webhook")
app.include_router(gmail_router, prefix="/webhook")
app.include_router(slack_router, prefix="/webhook")
app.include_router(discord_route_router, prefix="/webhook")
app.include_router(sms_router)  # has /webhook/twilio inside
app.include_router(internal_router, prefix="/internal")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

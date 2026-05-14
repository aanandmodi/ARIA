"""
Morning briefing worker.
"""
from __future__ import annotations
import asyncio
from api.core.config import settings
from api.core.logging import log
from api.llm.briefing import compose_briefing
from api.services import telegram_service, weather_service, calendar_service
from api.services import stocks_service, hn_service, github_service

async def send_morning_briefing(ctx: dict) -> None:
    """Gather data and send the morning briefing to Telegram."""
    log.info("briefing_starting")
    try:
        results = await asyncio.gather(
            weather_service.get_forecast(),
            calendar_service.get_today_events(),
            stocks_service.get_prices(settings.stock_list) if settings.stock_list else _empty_dict(),
            stocks_service.get_crypto(settings.crypto_list) if settings.crypto_list else _empty_dict(),
            hn_service.get_top(n=3),
            github_service.get_digest() if settings.github_token else _empty_str(),
            return_exceptions=True,
        )
        weather_data = results[0] if not isinstance(results[0], Exception) else {}
        events = results[1] if not isinstance(results[1], Exception) else []
        stocks = results[2] if not isinstance(results[2], Exception) else {}
        crypto = results[3] if not isinstance(results[3], Exception) else {}
        hn_stories = results[4] if not isinstance(results[4], Exception) else []
        github_digest = results[5] if not isinstance(results[5], Exception) else ""

        weather_str = weather_service.format_forecast(weather_data) if isinstance(weather_data, dict) else "N/A"
        events_str = "\n".join([f"• {e.summary} at {e.start}" for e in events]) if events else "No events"
        markets_str = stocks_service.format_prices(stocks, crypto)
        hn_str = hn_service.format_stories(hn_stories) if isinstance(hn_stories, list) else "N/A"

        briefing = await compose_briefing(
            weather=weather_str, events=events_str, emails="Check inbox",
            whatsapp="Check messages", reminders="Check reminders",
            markets=markets_str, hn=hn_str, github=github_digest if isinstance(github_digest, str) else "",
        )
        await telegram_service.send_message(briefing)
        log.info("briefing_sent")
    except Exception as exc:
        log.error("briefing_failed", error=str(exc))
        await telegram_service.send_message("☀️ Good morning! Briefing generation encountered an error.")

async def _empty_dict():
    return {}

async def _empty_str():
    return ""

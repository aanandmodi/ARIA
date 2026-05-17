"""
Morning briefing worker - Enhanced with personalization and news scraping.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from api.core.config import settings
from api.core.logging import log
from api.db.session import async_session_factory
from api.llm.briefing import compose_briefing
from api.services import telegram_service, weather_service, calendar_service
from api.services import stocks_service, hn_service, github_service
from api.services.news_scraper import scrape_news, format_news
from api.services.onboarding import get_user_profile


async def send_morning_briefing(ctx: dict) -> None:
    """
    Gather data and send personalized morning briefing to Telegram.
    Enhanced with:
    - Personalized greeting
    - Scraped news content
    - User profile integration
    - Unread message summary
    """
    log.info("briefing_starting")
    
    try:
        # Get user profile for personalization
        async with async_session_factory() as db:
            profile = await get_user_profile(db)
        
        user_name = profile.get("name", "there")
        user_location = profile.get("location", settings.timezone)
        
        # Personalized greeting based on time
        tz = ZoneInfo(settings.timezone)
        now = datetime.now(tz)
        hour = now.hour
        
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Gather all data in parallel
        results = await asyncio.gather(
            weather_service.get_forecast(),
            calendar_service.get_today_events(),
            stocks_service.get_prices(settings.stock_list) if settings.stock_list else _empty_dict(),
            stocks_service.get_crypto(settings.crypto_list) if settings.crypto_list else _empty_dict(),
            scrape_news(limit=5),  # Scrape actual news content
            github_service.get_digest() if settings.github_token else _empty_str(),
            _get_unread_summary(),
            return_exceptions=True,
        )
        
        weather_data = results[0] if not isinstance(results[0], Exception) else {}
        events = results[1] if not isinstance(results[1], Exception) else []
        stocks = results[2] if not isinstance(results[2], Exception) else {}
        crypto = results[3] if not isinstance(results[3], Exception) else {}
        news_items = results[4] if not isinstance(results[4], Exception) else []
        github_digest = results[5] if not isinstance(results[5], Exception) else ""
        unread_summary = results[6] if not isinstance(results[6], Exception) else ""
        
        # Format sections
        weather_str = weather_service.format_forecast(weather_data) if isinstance(weather_data, dict) else "Weather unavailable"
        
        events_str = "No events scheduled"
        if events:
            events_str = "\n".join([f"• {e.summary} at {e.start}" for e in events])
        
        markets_str = stocks_service.format_prices(stocks, crypto) if (stocks or crypto) else "Markets data unavailable"
        
        news_str = format_news(news_items) if news_items else "No news available"
        
        # Build enhanced briefing
        briefing = f"""
{greeting}, {user_name}! ☀️

<b>🌤 Weather in {user_location}</b>
{weather_str}

<b>📅 Today's Schedule</b>
{events_str}

<b>📰 Top News</b>
{news_str}

<b>📈 Markets</b>
{markets_str}

<b>📬 Unread Messages</b>
{unread_summary}
"""
        
        # Add GitHub section if available
        if github_digest:
            briefing += f"\n<b>🐙 GitHub</b>\n{github_digest}\n"
        
        briefing += "\nHave a great day! 🚀"
        
        await telegram_service.send_message(briefing)
        log.info("briefing_sent", user=user_name)
        
    except Exception as exc:
        log.error("briefing_failed", error=str(exc))
        await telegram_service.send_message("☀️ Good morning! Briefing generation encountered an error.")


async def _get_unread_summary() -> str:
    """Get summary of unread messages."""
    try:
        from sqlalchemy import select, func
        from api.db.models import Message
        
        async with async_session_factory() as db:
            # Count unread messages by platform
            result = await db.execute(
                select(
                    Message.platform,
                    func.count(Message.id).label('count')
                ).where(
                    Message.silenced == False
                ).group_by(Message.platform)
            )
            
            counts = result.all()
            
            if not counts:
                return "No unread messages"
            
            lines = []
            for platform, count in counts:
                emoji = {
                    "gmail": "📧",
                    "whatsapp": "💬",
                    "discord": "🎮",
                    "slack": "🟡",
                    "sms": "📱"
                }.get(platform, "📨")
                
                lines.append(f"{emoji} {platform.title()}: {count}")
            
            return "\n".join(lines)
    except Exception as exc:
        log.error("unread_summary_failed", error=str(exc))
        return "Unable to fetch unread messages"


async def _empty_dict():
    return {}


async def _empty_str():
    return ""

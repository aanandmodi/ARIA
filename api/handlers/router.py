"""
Intent dispatcher — routes parsed intents to the correct handler.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.llm.intent import IntentResult
from api.llm.client import chat
from api.llm.prompts import GENERAL_SYSTEM
from api.services import telegram_service
from api.core.logging import log

async def dispatch(intent: IntentResult, db: AsyncSession, update: Update) -> None:
    """Route an IntentResult to the correct handler."""
    from api.handlers import reply_handler, reminder_handler, search_handler, email_handler
    from api.handlers import schedule_handler, note_handler, expense_handler
    from api.handlers import habit_handler, spotify_handler, summary_handler

    text = update.message.text if update.message else ""

    match intent.intent:
        case "reply":
            await reply_handler.handle(intent.params, db, update)
        case "compose_email":
            await email_handler.handle(intent.params, db, update)
        case "reminder":
            await reminder_handler.handle(intent.params, db, update)
        case "search":
            await search_handler.handle(intent.params, db, update)
        case "schedule":
            await schedule_handler.handle(intent.params, db, update)
        case "note":
            await note_handler.handle(intent.params, db, update)
        case "expense":
            await expense_handler.handle(intent.params, db, update)
        case "habit":
            await habit_handler.handle(intent.params, db, update)
        case "spotify":
            await spotify_handler.handle(intent.params, db, update)
        case "weather":
            from api.services import weather_service
            forecast = await weather_service.get_forecast()
            response = weather_service.format_forecast(forecast)
            await telegram_service.send_message(f"🌤 <b>Weather Forecast</b>\n\n{response}")
        case "summary":
            await summary_handler.handle(intent.params, db, update)
        case "github":
            from api.services import github_service
            action = intent.params.get("action", "notifications")
            if action == "notifications":
                notifs = await github_service.get_notifications()
                if notifs:
                    lines = ["🐙 <b>GitHub Notifications</b>\n"]
                    for n in notifs:
                        lines.append(f"• <b>{n['type']}</b>: {n['title']} ({n['repo']})")
                    await telegram_service.send_message("\n".join(lines))
                else:
                    await telegram_service.send_message("🐙 No unread GitHub notifications.")
            else:
                digest = await github_service.get_digest()
                await telegram_service.send_message(f"🐙 <b>GitHub Digest</b>\n\n{digest}")
        case "briefing":
            from api.workers.briefing import send_morning_briefing
            await send_morning_briefing({})
        case "markets":
            from api.handlers import markets_handler
            await markets_handler.handle(intent.params, db, update)
        case "websearch":
            from api.handlers import websearch_handler
            await websearch_handler.handle(intent.params, db, update)
        case _:
            # General question — ask Groq
            answer = await chat(text, system=GENERAL_SYSTEM, max_tokens=1024)
            if answer:
                await telegram_service.send_message(answer)
            else:
                await telegram_service.send_message("🤔 I'm not sure how to help with that. Try rephrasing?")

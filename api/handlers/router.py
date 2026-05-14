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
        case "github_action":
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
            elif action == "prs":
                digest = await github_service.get_digest()
                await telegram_service.send_message(f"🐙 <b>GitHub PRs/Issues</b>\n\n{digest}")
            elif action == "merge":
                repo = intent.params.get("repo")
                number = intent.params.get("number")
                if repo and number:
                    res = await github_service.merge_pr(repo, int(number))
                    await telegram_service.send_message("✅ PR Merged!" if res else "❌ Failed to merge PR.")
                else:
                    await telegram_service.send_message("⚠️ Please specify repo and PR number.")
            elif action == "close":
                repo = intent.params.get("repo")
                number = intent.params.get("number")
                if repo and number:
                    res = await github_service.close_issue(repo, int(number))
                    await telegram_service.send_message("✅ Issue/PR Closed!" if res else "❌ Failed to close.")
                else:
                    await telegram_service.send_message("⚠️ Please specify repo and issue number.")
            elif action == "comment":
                repo = intent.params.get("repo")
                number = intent.params.get("number")
                text_ = intent.params.get("text")
                if repo and number and text_:
                    res = await github_service.comment_issue(repo, int(number), text_)
                    await telegram_service.send_message("✅ Commented!" if res else "❌ Failed to comment.")
                else:
                    await telegram_service.send_message("⚠️ Please specify repo, issue number, and comment text.")
            elif action == "create_issue":
                repo = intent.params.get("repo")
                text_ = intent.params.get("text")
                if repo and text_:
                    url = await github_service.create_issue(repo, text_)
                    await telegram_service.send_message(f"✅ Issue created: {url}" if url else "❌ Failed to create issue.")
                else:
                    await telegram_service.send_message("⚠️ Please specify repo and issue title.")
            else:
                digest = await github_service.get_digest()
                await telegram_service.send_message(f"🐙 <b>GitHub Digest</b>\n\n{digest}")
        case "create_memory":
            from api.db.models import Memory
            fact = intent.params.get("fact")
            entity = intent.params.get("entity", "user")
            if fact:
                db.add(Memory(
                    entity_type="user_fact",
                    entity_key=entity or "user",
                    fact=fact,
                    confidence=1.0,
                    source="explicit",
                ))
                await db.flush()
                await telegram_service.send_message(f"🧠 I'll remember that: {fact}")
            else:
                await telegram_service.send_message("⚠️ Could not extract fact to remember.")
        case "send_sms":
            from api.adapters.sms_adapter import SmsAdapter
            to = intent.params.get("to")
            msg = intent.params.get("message")
            if to and msg:
                adapter = SmsAdapter()
                res = await adapter.send_message(to, msg)
                await telegram_service.send_message("✉️ SMS sent!" if res else "❌ Failed to send SMS.")
            else:
                await telegram_service.send_message("⚠️ Please specify recipient and message.")
        case "system_status":
            from api.core.queue import get_redis
            from sqlalchemy import text as sql_text
            status_lines = ["🟢 <b>ARIA System Status</b>\n"]
            # DB check
            try:
                await db.execute(sql_text("SELECT 1"))
                status_lines.append("✅ PostgreSQL: connected")
            except Exception:
                status_lines.append("❌ PostgreSQL: unreachable")
            # Redis check
            try:
                redis = await get_redis()
                await redis.ping()
                status_lines.append("✅ Redis: connected")
            except Exception:
                status_lines.append("❌ Redis: unreachable")
            # Memory count
            try:
                from api.db.models import Memory, Message as MsgModel, Contact as ContactModel
                from sqlalchemy import func as sql_func
                mem_count = (await db.execute(sql_text("SELECT count(*) FROM memories"))).scalar() or 0
                msg_count = (await db.execute(sql_text("SELECT count(*) FROM messages"))).scalar() or 0
                contact_count = (await db.execute(sql_text("SELECT count(*) FROM contacts"))).scalar() or 0
                status_lines.append(f"\n📊 <b>Data</b>")
                status_lines.append(f"• Messages: {msg_count}")
                status_lines.append(f"• Contacts: {contact_count}")
                status_lines.append(f"• Memories: {mem_count}")
            except Exception:
                pass
            await telegram_service.send_message("\n".join(status_lines))
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
            # General question — ask Groq with personal context + memory
            try:
                from api.llm.personal_context import build_system_prompt
                from api.core.queue import get_redis
                redis = await get_redis()
                system_prompt = await build_system_prompt(db, redis, query_text=text)
            except Exception as ctx_exc:
                log.warning("personal_context_fallback", error=str(ctx_exc))
                system_prompt = GENERAL_SYSTEM
            answer = await chat(text, system=system_prompt, max_tokens=1024)
            if answer:
                await telegram_service.send_message(answer)
                # Extract memories from this exchange
                try:
                    from api.llm.memory_extractor import extract_and_store
                    await extract_and_store(text, answer, db)
                except Exception:
                    pass
            else:
                await telegram_service.send_message("🤔 I'm not sure how to help with that. Try rephrasing?")

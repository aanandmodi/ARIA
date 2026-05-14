"""
Reply handler — routes outbound replies to the correct platform.
Implements the full 10-step reply flow including draft mode.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from api.core.config import settings
from api.core.logging import log
from api.core.queue import enqueue, get_redis
from api.db.models import Message, TelegramSession
from api.llm.format_reply import format_reply
from api.services import telegram_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle reply intent from user."""
    reply_text = params.get("text", "")
    if not reply_text and update.message:
        reply_text = update.message.text or ""
    if not reply_text:
        await telegram_service.send_message("❌ No reply text provided.")
        return

    user_id = settings.telegram_user_id

    # 1. Read session
    result = await db.execute(select(TelegramSession).where(TelegramSession.user_id == user_id))
    session = result.scalar_one_or_none()

    if not session or session.state == "idle" or not session.last_message_id:
        await telegram_service.send_message("💬 No active message to reply to. Tap Reply on a notification first.")
        return

    # 2. If awaiting approval, treat as approval
    if session.state == "awaiting_approval":
        await _send_approved_reply(session, db)
        return

    # 3. Get the original message
    try:
        msg_id = uuid.UUID(session.last_message_id)
    except ValueError:
        await telegram_service.send_message("❌ Invalid message reference.")
        return

    result = await db.execute(select(Message).where(Message.id == msg_id))
    original = result.scalar_one_or_none()
    if not original:
        await telegram_service.send_message("❌ Original message not found.")
        return

    # 4. Format reply
    formatted = await format_reply(reply_text, original.platform, original.sender_name or "Unknown", original.content[:500])

    # 5. Draft mode check
    if settings.draft_mode:
        session.draft_content = formatted
        session.state = "awaiting_approval"
        await db.flush()
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{session.last_message_id}"),
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit:{session.last_message_id}"),
        ]])
        await telegram_service.send_message(f"📝 <b>Draft reply to {original.sender_name}:</b>\n\n{formatted}", reply_markup=keyboard)
        return

    # 6. Send directly
    await _route_reply(original, formatted, db)
    session.state = "idle"
    session.last_message_id = None
    await db.flush()


async def _send_approved_reply(session: TelegramSession, db: AsyncSession) -> None:
    """Send the previously drafted reply."""
    if not session.draft_content or not session.last_message_id:
        await telegram_service.send_message("❌ No draft to approve.")
        return
    try:
        msg_id = uuid.UUID(session.last_message_id)
    except ValueError:
        return
    result = await db.execute(select(Message).where(Message.id == msg_id))
    original = result.scalar_one_or_none()
    if not original:
        await telegram_service.send_message("❌ Original message not found.")
        return
    await _route_reply(original, session.draft_content, db)
    session.state = "idle"
    session.draft_content = None
    session.last_message_id = None
    await db.flush()


async def _route_reply(original: Message, text: str, db: AsyncSession) -> None:
    """Route the formatted reply to the correct platform."""
    platform = original.platform
    success = False
    try:
        if platform == "gmail":
            from api.services import gmail_service
            subject = f"Re: {original.raw.get('subject', '')}" if original.raw.get("subject") else "Re:"
            thread_id = original.raw.get("thread_id", "")
            await gmail_service.send_email(original.sender_id, subject, text, thread_id=thread_id or None)
            success = True
        elif platform == "whatsapp":
            from api.services import whatsapp_service
            jid = original.raw.get("jid", original.sender_id)
            if "@" not in jid:
                jid = f"{jid}@s.whatsapp.net"
            await whatsapp_service.send_message(jid, text)
            success = True
        elif platform == "discord":
            from api.services import discord_service
            channel_id = original.raw.get("channel_id", "")
            if channel_id:
                await discord_service.send_message(channel_id, text)
                success = True
        elif platform == "slack":
            from api.services import slack_service
            channel = original.raw.get("event", {}).get("channel", "")
            if channel:
                await slack_service.send_message(channel, text)
                success = True
        elif platform == "sms":
            from api.services import sms_service
            await sms_service.send_sms(original.sender_id, text)
            success = True
        else:
            await telegram_service.send_message(f"⚠️ Reply to {platform} not supported yet.")
            return
    except Exception as exc:
        log.error("reply_route_failed", error=str(exc), platform=platform)
        await telegram_service.send_message(f"❌ Failed to send reply via {platform}.")
        return

    if success:
        original.replied_at = datetime.utcnow()
        await db.flush()
        # Cancel follow-up if exists
        try:
            redis = await get_redis()
            await redis.delete(f"followup:{original.id}")
        except Exception:
            pass
        # Update notification message
        if original.telegram_msg_id:
            await telegram_service.edit_message(original.telegram_msg_id, f"✓ Replied via {platform}")
        await telegram_service.send_message(f"✅ Reply sent via {platform} to {original.sender_name}!")
        log.info("reply_sent", platform=platform, recipient=original.sender_id)


async def handle_callback(callback: CallbackQuery, db: AsyncSession) -> None:
    """Handle inline keyboard button presses from notifications."""
    data = callback.data or ""
    parts = data.split(":", 1)
    if len(parts) != 2:
        await telegram_service.answer_callback(callback.id, "Invalid action")
        return

    action, msg_id_str = parts
    user_id = settings.telegram_user_id

    if action == "reply":
        # Set session to awaiting_reply
        result = await db.execute(select(TelegramSession).where(TelegramSession.user_id == user_id))
        session = result.scalar_one_or_none()
        if not session:
            session = TelegramSession(user_id=user_id)
            db.add(session)
        session.last_message_id = msg_id_str
        session.state = "awaiting_reply"
        # Look up platform
        try:
            result = await db.execute(select(Message).where(Message.id == uuid.UUID(msg_id_str)))
            msg = result.scalar_one_or_none()
            session.last_platform = msg.platform if msg else None
        except Exception:
            pass
        await db.flush()
        await telegram_service.answer_callback(callback.id, "Type your reply now")
        await telegram_service.send_message("💬 Type your reply now — I'll format and send it.")

    elif action == "dismiss":
        try:
            result = await db.execute(select(Message).where(Message.id == uuid.UUID(msg_id_str)))
            msg = result.scalar_one_or_none()
            if msg:
                msg.silenced = True
                await db.flush()
        except Exception:
            pass
        await telegram_service.answer_callback(callback.id, "Dismissed ✓")
        if callback.message:
            await telegram_service.edit_message(callback.message.message_id, "🔇 Dismissed")

    elif action == "snooze":
        await telegram_service.answer_callback(callback.id, "Snoozed for 1 hour")
        await enqueue("process_inbound_message", {"snooze_msg_id": msg_id_str}, _defer_by=3600)
        if callback.message:
            await telegram_service.edit_message(callback.message.message_id, "⏰ Snoozed — will remind in 1 hour")

    elif action == "approve":
        result = await db.execute(select(TelegramSession).where(TelegramSession.user_id == user_id))
        session = result.scalar_one_or_none()
        if session and session.state == "awaiting_approval":
            await _send_approved_reply(session, db)
        await telegram_service.answer_callback(callback.id, "Approved ✓")

    elif action == "edit":
        result = await db.execute(select(TelegramSession).where(TelegramSession.user_id == user_id))
        session = result.scalar_one_or_none()
        if session:
            session.state = "awaiting_reply"
            session.draft_content = None
            await db.flush()
        await telegram_service.answer_callback(callback.id, "Send your edited reply")
        await telegram_service.send_message("✏️ Type your edited reply:")
    else:
        await telegram_service.answer_callback(callback.id)

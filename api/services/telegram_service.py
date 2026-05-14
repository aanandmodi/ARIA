"""
Telegram service — send, edit, notify via python-telegram-bot.
"""

from __future__ import annotations

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction, ParseMode

from api.core.config import settings
from api.core.logging import log

# Lazy bot singleton
_bot: Bot | None = None

PLATFORM_EMOJI: dict[str, str] = {
    "gmail": "📧",
    "whatsapp": "💬",
    "discord": "🎮",
    "slack": "🟡",
    "sms": "📱",
    "rss": "📰",
    "github": "🐙",
    "reddit": "🔴",
    "hn": "📰",
}


def _importance_emoji(score: int) -> str:
    if score >= 7:
        return "🔴"
    elif score >= 4:
        return "🟡"
    return "⚪"


def get_bot() -> Bot:
    """Return (and lazily create) the Telegram Bot instance."""
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


async def send_message(
    text: str,
    parse_mode: str = ParseMode.HTML,
    reply_markup: InlineKeyboardMarkup | None = None,
    chat_id: int | None = None,
) -> int:
    """Send a message to the configured Telegram user. Returns message_id."""
    try:
        bot = get_bot()
        target = chat_id or settings.telegram_user_id
        msg = await bot.send_message(
            chat_id=target,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        log.info("telegram_sent", msg_id=msg.message_id, length=len(text))
        return msg.message_id
    except Exception as exc:
        log.error("telegram_send_failed", error=str(exc))
        return 0


async def edit_message(
    message_id: int,
    new_text: str,
    parse_mode: str = ParseMode.HTML,
    reply_markup: InlineKeyboardMarkup | None = None,
    chat_id: int | None = None,
) -> None:
    """Edit a previously sent bot message."""
    try:
        bot = get_bot()
        target = chat_id or settings.telegram_user_id
        await bot.edit_message_text(
            chat_id=target,
            message_id=message_id,
            text=new_text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        log.info("telegram_edited", msg_id=message_id)
    except Exception as exc:
        log.error("telegram_edit_failed", error=str(exc), msg_id=message_id)


import re

async def send_notification(
    msg_id: str,
    platform: str,
    sender_name: str,
    summary: str,
    importance: int,
    category: str,
    urgency: str,
    subject: str | None = None,
    content: str | None = None,
    quick_replies: list[str] | None = None,
) -> int:
    """
    Build and send a formatted notification for an inbound message.
    Returns the Telegram message_id.
    """
    emoji = PLATFORM_EMOJI.get(platform, "📨")
    imp_emoji = _importance_emoji(importance)

    lines = [
        f"{emoji} <b>{_escape_html(sender_name)}</b>",
    ]
    if subject:
        lines.append(f"📌 <i>{_escape_html(subject)}</i>")
    
    # OTP Extraction
    otp_match = None
    if content:
        otp_match = re.search(r'\b(\d{4,8})\b', content)
        if otp_match and ('code' in content.lower() or 'otp' in content.lower() or 'verification' in content.lower()):
            lines.append(f"🔑 <b>OTP:</b> <code>{otp_match.group(1)}</code>")
    
    lines.append("")
    if content and len(content) < 200:
        lines.append(_escape_html(content))
    else:
        lines.append(_escape_html(summary))
        if content:
            lines.append("")
            lines.append(f"<i>Snippet: {_escape_html(content[:150])}...</i>")
    
    lines.append("")
    lines.append(
        f"{imp_emoji} Importance {importance}/10 · {category} · {urgency}"
    )

    text = "\n".join(lines)

    buttons = [
        [
            InlineKeyboardButton("💬 Reply", callback_data=f"reply:{msg_id}"),
            InlineKeyboardButton("🔇 Dismiss", callback_data=f"dismiss:{msg_id}"),
            InlineKeyboardButton("⏰ Snooze 1h", callback_data=f"snooze:{msg_id}"),
        ]
    ]
    
    if quick_replies:
        for qr in quick_replies:
            # We must keep callback_data under 64 bytes. qr itself might be up to ~40 bytes
            # Format: 'qr:{msg_id}:{text[:20]}' - actually it's easier to store the qr in a cache or just put it in the callback if it's small.
            # "qr:{msg_id}:{text}"
            cb_data = f"qr:{msg_id}:{qr}"
            if len(cb_data.encode('utf-8')) <= 64:
                buttons.append([InlineKeyboardButton(f"⚡ {qr}", callback_data=cb_data)])

    keyboard = InlineKeyboardMarkup(buttons)

    return await send_message(text, reply_markup=keyboard)


async def send_typing(chat_id: int | None = None) -> None:
    """Send typing action indicator."""
    try:
        bot = get_bot()
        target = chat_id or settings.telegram_user_id
        await bot.send_chat_action(chat_id=target, action=ChatAction.TYPING)
    except Exception as exc:
        log.error("telegram_typing_failed", error=str(exc))


async def send_document(
    file_bytes: bytes,
    filename: str,
    caption: str = "",
    chat_id: int | None = None,
) -> None:
    """Send a file attachment to the user."""
    try:
        import io
        bot = get_bot()
        target = chat_id or settings.telegram_user_id
        bio = io.BytesIO(file_bytes)
        bio.name = filename
        await bot.send_document(
            chat_id=target,
            document=bio,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        log.info("telegram_doc_sent", filename=filename)
    except Exception as exc:
        log.error("telegram_doc_failed", error=str(exc))


async def answer_callback(callback_query_id: str, text: str = "") -> None:
    """Answer a Telegram callback query."""
    try:
        bot = get_bot()
        await bot.answer_callback_query(callback_query_id, text=text)
    except Exception as exc:
        log.error("telegram_callback_answer_failed", error=str(exc))


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

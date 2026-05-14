"""
Email handler — composing and sending new emails via Gmail.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, gmail_service
from api.core.logging import log
from api.core.config import settings

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    to = params.get("to")
    subject = params.get("subject", "Message from ARIA")
    body = params.get("body", "")

    if not to or not body:
        await telegram_service.send_message("❌ Please provide both a recipient email address and the message body to send an email.")
        return

    await telegram_service.send_message(f"📧 Sending email to <b>{to}</b>...")

    try:
        if settings.draft_mode:
            draft_id = await gmail_service.create_draft(to=to, subject=subject, body=body)
            if draft_id:
                await telegram_service.send_message(f"✅ Draft created successfully!\n\n<b>To:</b> {to}\n<b>Subject:</b> {subject}\n\n<i>{body}</i>")
            else:
                await telegram_service.send_message("❌ Failed to create email draft.")
        else:
            msg_id = await gmail_service.send_email(to=to, subject=subject, body=body)
            if msg_id:
                await telegram_service.send_message(f"✅ Email sent successfully!\n\n<b>To:</b> {to}\n<b>Subject:</b> {subject}\n\n<i>{body}</i>")
            else:
                await telegram_service.send_message("❌ Failed to send email.")
    except Exception as exc:
        log.error("email_handler_error", error=str(exc))
        await telegram_service.send_message("❌ An error occurred while trying to send the email.")

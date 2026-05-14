"""
Core inbound message processing worker.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import select
from api.adapters.base import InboundMessage
from api.core.config import settings
from api.core.logging import log
from api.core.queue import enqueue
from api.db.models import Contact, Message, Thread
from api.db.session import get_db_session
from api.llm.classify import classify
from api.llm.transcribe import transcribe
from api.services import telegram_service


async def process_inbound_message(ctx: dict, msg_dict: dict) -> None:
    """Process every inbound message. Runs in ARQ worker."""
    # Handle snooze re-notification
    if "snooze_msg_id" in msg_dict:
        await _handle_snooze(msg_dict["snooze_msg_id"])
        return

    msg = InboundMessage.from_dict(msg_dict)
    log.info("processing_inbound", platform=msg.platform, sender=msg.sender_id)

    async with get_db_session() as db:
        # 0. Gmail: fetch real message ID if we only have historyId
        if msg.platform == "gmail" and not msg.content:
            from api.services.gmail_service import get_latest_message_id
            latest_id = await get_latest_message_id()
            if latest_id:
                msg.message_id = latest_id
            else:
                log.warning("gmail_latest_id_not_found")

        # 1. Idempotency check
        if msg.message_id:
            existing = await db.execute(
                select(Message).where(Message.external_id == msg.message_id)
            )
            if existing.scalar_one_or_none():
                log.info("duplicate_skipped", external_id=msg.message_id)
                return

        # 2. Gmail: fetch full body
        if msg.platform == "gmail" and not msg.content:
            try:
                from api.services.gmail_service import fetch_full_message
                full = await fetch_full_message(msg.message_id)
                if full:
                    msg.content = full.body
                    msg.subject = full.subject
                    msg.sender_name = full.sender_name
                    msg.sender_id = full.sender
            except Exception as exc:
                log.error("gmail_fetch_in_worker_failed", error=str(exc))

        # 3. Voice note transcription
        if msg.audio_url:
            try:
                from api.services.minio_service import download
                audio_bytes = await download(msg.audio_url)
                if audio_bytes:
                    transcript = await transcribe(audio_bytes)
                    msg.content = f"[Voice note]: {transcript}"
            except Exception as exc:
                log.error("transcription_in_worker_failed", error=str(exc))

        # 4. Classify
        result = await classify(msg.platform, msg.sender_id, msg.sender_name, msg.content)

        # 5. Upsert contact
        contact = await _upsert_contact(db, msg, result)

        # 6. Upsert thread
        thread = await _upsert_thread(db, msg)

        # 7. Persist message
        db_msg = Message(
            platform=msg.platform,
            external_id=msg.message_id,
            thread_id=thread.id if thread else None,
            sender_id=msg.sender_id,
            sender_name=msg.sender_name,
            content=msg.content,
            summary=result.summary,
            importance=result.importance,
            category=result.category,
            needs_reply=result.needs_reply,
            urgency=result.urgency,
            has_attachment=msg.has_attachment,
            attachment_urls=msg.attachment_urls,
            raw=msg.raw,
        )
        db.add(db_msg)
        await db.flush()
        await db.refresh(db_msg)

        # 8. Score gate — notify if important enough
        if result.importance >= settings.importance_threshold:
            tg_msg_id = await telegram_service.send_notification(
                msg_id=str(db_msg.id),
                platform=msg.platform,
                sender_name=msg.sender_name,
                summary=result.summary,
                importance=result.importance,
                category=result.category,
                urgency=result.urgency,
                subject=msg.subject,
            )
            db_msg.telegram_msg_id = tg_msg_id
            await db.flush()

        # 9. Schedule follow-up if needs reply
        if result.needs_reply:
            defer_seconds = settings.follow_up_days * 86400
            await enqueue(
                "check_single_followup",
                str(db_msg.id),
                _defer_by=defer_seconds,
            )

        log.info(
            "inbound_processed",
            platform=msg.platform,
            sender=msg.sender_id,
            importance=result.importance,
            category=result.category,
        )


async def _upsert_contact(db, msg: InboundMessage, result) -> Contact:
    """Find or create a contact for this sender."""
    stmt = select(Contact).where(Contact.email == msg.sender_id)
    existing = await db.execute(stmt)
    contact = existing.scalar_one_or_none()

    if not contact:
        stmt2 = select(Contact).where(Contact.phone == msg.sender_id)
        existing2 = await db.execute(stmt2)
        contact = existing2.scalar_one_or_none()

    if contact:
        contact.message_count += 1
        contact.last_seen = datetime.utcnow()
        if msg.sender_name and msg.sender_name != msg.sender_id:
            contact.name = msg.sender_name
        pids = contact.platform_ids or {}
        pids[msg.platform] = msg.sender_id
        contact.platform_ids = pids
        await db.flush()
    else:
        contact = Contact(
            name=msg.sender_name,
            email=msg.sender_id if "@" in msg.sender_id else None,
            phone=msg.sender_id if "@" not in msg.sender_id and msg.platform in ("whatsapp", "sms") else None,
            platform_ids={msg.platform: msg.sender_id},
            message_count=1,
            last_seen=datetime.utcnow(),
        )
        db.add(contact)
        await db.flush()
    return contact


async def _upsert_thread(db, msg: InboundMessage) -> Thread | None:
    """Find or create a thread for this conversation."""
    if not msg.thread_id:
        return None
    stmt = select(Thread).where(
        Thread.platform == msg.platform,
        Thread.external_thread_id == msg.thread_id,
    )
    existing = await db.execute(stmt)
    thread = existing.scalar_one_or_none()
    if thread:
        thread.message_count += 1
        thread.last_msg_at = datetime.utcnow()
        await db.flush()
    else:
        thread = Thread(
            platform=msg.platform,
            external_thread_id=msg.thread_id,
            subject=msg.subject,
            last_msg_at=datetime.utcnow(),
            message_count=1,
        )
        db.add(thread)
        await db.flush()
    return thread


async def _handle_snooze(msg_id_str: str) -> None:
    """Re-send notification for a snoozed message."""
    async with get_db_session() as db:
        try:
            result = await db.execute(
                select(Message).where(Message.id == uuid.UUID(msg_id_str))
            )
            msg = result.scalar_one_or_none()
            if msg and not msg.silenced:
                await telegram_service.send_notification(
                    msg_id=str(msg.id),
                    platform=msg.platform,
                    sender_name=msg.sender_name or "Unknown",
                    summary=msg.summary or msg.content[:100],
                    importance=msg.importance or 5,
                    category=msg.category or "unknown",
                    urgency=msg.urgency or "whenever",
                    subject=msg.raw.get("subject"),
                )
        except Exception as exc:
            log.error("snooze_resend_failed", error=str(exc))

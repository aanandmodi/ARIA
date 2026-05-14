"""
WhatsApp adapter — parses Baileys event payloads into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(raw_payload: dict) -> InboundMessage | None:
    """
    Parse a Baileys webhook event into an InboundMessage.
    Handles text, audio, image, and document message types.
    """
    try:
        jid = raw_payload.get("jid", "")
        push_name = raw_payload.get("pushName", "")
        msg_type = raw_payload.get("messageType", "text")
        message_id = raw_payload.get("messageId", "")

        # Extract text content based on message type
        content = ""
        audio_url = None
        has_attachment = False
        attachment_urls: list[str] = []

        if msg_type == "text" or msg_type == "conversation":
            content = raw_payload.get("text", "") or raw_payload.get("conversation", "")
        elif msg_type == "audio":
            audio_url = raw_payload.get("mediaUrl", "")
            content = "[Voice note]"
            has_attachment = True
        elif msg_type == "image":
            content = raw_payload.get("caption", "[Image]")
            media_url = raw_payload.get("mediaUrl", "")
            if media_url:
                attachment_urls.append(media_url)
            has_attachment = True
        elif msg_type == "document":
            content = raw_payload.get("caption", "[Document]")
            media_url = raw_payload.get("mediaUrl", "")
            if media_url:
                attachment_urls.append(media_url)
            has_attachment = True
        elif msg_type == "extendedText":
            content = raw_payload.get("text", "")
        else:
            content = raw_payload.get("text", f"[{msg_type} message]")

        if not jid:
            log.warning("whatsapp_adapter_no_jid", payload=raw_payload)
            return None

        # Extract phone number from JID (format: 91xxxxxxxxxx@s.whatsapp.net)
        phone = jid.split("@")[0] if "@" in jid else jid

        return InboundMessage(
            platform="whatsapp",
            message_id=message_id or f"wa_{datetime.utcnow().timestamp()}",
            thread_id=jid,
            sender_id=phone,
            sender_name=push_name or phone,
            content=content,
            raw=raw_payload,
            received_at=datetime.utcnow(),
            has_attachment=has_attachment,
            attachment_urls=attachment_urls,
            audio_url=audio_url,
        )
    except Exception as exc:
        log.error("whatsapp_adapter_parse_error", error=str(exc))
        return None

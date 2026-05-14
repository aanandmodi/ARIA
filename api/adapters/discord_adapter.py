"""
Discord adapter — parses discord.py Message objects into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(raw_payload: dict) -> InboundMessage | None:
    """
    Parse a Discord message (serialised dict from discord.py) into InboundMessage.
    """
    try:
        author = raw_payload.get("author", {})
        author_id = str(author.get("id", ""))
        author_name = author.get("display_name", "") or author.get("name", "Unknown")
        content = raw_payload.get("content", "")
        message_id = str(raw_payload.get("id", ""))
        channel_id = str(raw_payload.get("channel_id", ""))
        guild_name = raw_payload.get("guild_name", "")

        if not content and not raw_payload.get("attachments"):
            log.debug("discord_adapter_empty_message", msg_id=message_id)
            return None

        # Handle attachments
        has_attachment = bool(raw_payload.get("attachments"))
        attachment_urls = [a.get("url", "") for a in raw_payload.get("attachments", []) if a.get("url")]

        if guild_name:
            channel_info = f"#{raw_payload.get('channel_name', channel_id)} in {guild_name}"
        else:
            channel_info = f"DM"

        return InboundMessage(
            platform="discord",
            message_id=message_id,
            thread_id=channel_id,
            sender_id=author_id,
            sender_name=f"{author_name} ({channel_info})",
            content=content,
            raw=raw_payload,
            received_at=datetime.utcnow(),
            has_attachment=has_attachment,
            attachment_urls=attachment_urls,
        )
    except Exception as exc:
        log.error("discord_adapter_parse_error", error=str(exc))
        return None

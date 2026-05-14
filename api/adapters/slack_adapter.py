"""
Slack adapter — parses Slack Events API payloads into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(raw_payload: dict) -> InboundMessage | None:
    """
    Parse a Slack Events API 'message' event into InboundMessage.
    Only processes message events (ignores subtypes like message_changed).
    """
    try:
        event = raw_payload.get("event", raw_payload)

        if event.get("type") != "message":
            return None

        # Skip bot messages and message subtypes (edits, deletes, etc.)
        if event.get("subtype") or event.get("bot_id"):
            return None

        user_id = event.get("user", "")
        text = event.get("text", "")
        channel = event.get("channel", "")
        ts = event.get("ts", "")
        thread_ts = event.get("thread_ts")

        if not user_id or not text:
            log.debug("slack_adapter_empty_message")
            return None

        # Use user ID as sender — real name resolution would need Slack API call
        sender_name = raw_payload.get("user_name", user_id)

        return InboundMessage(
            platform="slack",
            message_id=ts,
            thread_id=thread_ts or ts,
            sender_id=user_id,
            sender_name=sender_name,
            content=text,
            raw=raw_payload,
            received_at=datetime.utcnow(),
        )
    except Exception as exc:
        log.error("slack_adapter_parse_error", error=str(exc))
        return None

"""
Gmail adapter — parses Gmail Pub/Sub push notifications into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(raw_payload: dict) -> InboundMessage | None:
    """
    Parse a Gmail Pub/Sub notification.
    The notification only contains emailAddress + historyId —
    full body is fetched later by the worker via Gmail API.
    """
    try:
        email_address = raw_payload.get("emailAddress", "")
        history_id = str(raw_payload.get("historyId", ""))

        if not email_address or not history_id:
            log.warning("gmail_adapter_missing_fields", payload=raw_payload)
            return None

        return InboundMessage(
            platform="gmail",
            message_id=history_id,
            thread_id=None,
            sender_id=email_address,
            sender_name=email_address.split("@")[0],
            content="",  # will be filled by worker after fetching full message
            raw=raw_payload,
            received_at=datetime.utcnow(),
            subject=None,  # will be filled by worker
        )
    except Exception as exc:
        log.error("gmail_adapter_parse_error", error=str(exc))
        return None

"""
RSS adapter — parses feedparser entries into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(entry: dict, feed_url: str = "", feed_title: str = "") -> InboundMessage | None:
    """
    Parse a feedparser entry dict into an InboundMessage.
    """
    try:
        title = entry.get("title", "Untitled")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        entry_id = entry.get("id", link or title)
        published = entry.get("published", "")

        content = f"{title}\n\n{summary}" if summary else title
        if link:
            content += f"\n\n🔗 {link}"

        return InboundMessage(
            platform="rss",
            message_id=entry_id,
            thread_id=feed_url,
            sender_id=feed_url,
            sender_name=feed_title or feed_url,
            content=content,
            raw=entry,
            received_at=datetime.utcnow(),
            subject=title,
        )
    except Exception as exc:
        log.error("rss_adapter_parse_error", error=str(exc))
        return None

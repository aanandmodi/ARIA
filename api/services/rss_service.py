"""
RSS service — fetch, parse, dedup via feedparser + Redis.
"""

from __future__ import annotations

import asyncio
from functools import partial

import feedparser

from api.adapters.base import InboundMessage
from api.adapters.rss_adapter import parse as rss_parse
from api.core.logging import log
from api.core.queue import get_redis


async def poll_and_process(feed_url: str) -> list[InboundMessage]:
    """
    Fetch an RSS feed, deduplicate entries via Redis, and return new messages.
    """
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(
            None, partial(feedparser.parse, feed_url)
        )

        feed_title = feed.feed.get("title", feed_url)
        redis = await get_redis()
        seen_key = f"rss_seen:{feed_url}"

        new_messages: list[InboundMessage] = []

        for entry in feed.entries[:20]:
            entry_id = entry.get("id") or entry.get("link") or entry.get("title", "")
            if not entry_id:
                continue

            # Check if already seen
            already_seen = await redis.sismember(seen_key, entry_id)
            if already_seen:
                continue

            # Mark as seen
            await redis.sadd(seen_key, entry_id)
            # Keep set from growing indefinitely — expire after 7 days
            await redis.expire(seen_key, 7 * 86400)

            msg = rss_parse(dict(entry), feed_url=feed_url, feed_title=feed_title)
            if msg:
                new_messages.append(msg)

        log.info("rss_polled", feed=feed_url, new_count=len(new_messages))
        return new_messages

    except Exception as exc:
        log.error("rss_poll_failed", error=str(exc), feed=feed_url)
        return []

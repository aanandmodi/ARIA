"""
Polling workers for RSS, Reddit, HackerNews, GitHub.
"""
from __future__ import annotations
from api.core.config import settings
from api.core.logging import log
from api.core.queue import enqueue

async def poll_rss_feeds(ctx: dict) -> None:
    """Poll all configured RSS feeds."""
    from api.services.rss_service import poll_and_process
    for url in settings.rss_feed_list:
        try:
            messages = await poll_and_process(url)
            for msg in messages:
                await enqueue("process_inbound_message", msg.to_dict())
        except Exception as exc:
            log.error("rss_poll_error", feed=url, error=str(exc))

async def poll_reddit(ctx: dict) -> None:
    """Poll Reddit for keyword matches."""
    from api.services.reddit_service import poll_subreddit
    keywords = settings.keyword_list
    subreddits = ["technology", "programming"]  # configurable
    for sub in subreddits:
        try:
            posts = await poll_subreddit(sub, keywords=keywords, limit=5)
            for p in posts:
                await enqueue("process_inbound_message", {
                    "platform": "reddit", "message_id": p["id"], "thread_id": p["subreddit"],
                    "sender_id": p["author"], "sender_name": p["author"],
                    "content": f"{p['title']}\n{p['selftext'][:500]}\n{p['url']}",
                    "raw": p, "received_at": __import__("datetime").datetime.utcnow().isoformat(),
                })
        except Exception as exc:
            log.error("reddit_poll_error", sub=sub, error=str(exc))

async def poll_hn(ctx: dict) -> None:
    """Poll HackerNews top stories."""
    from api.services.hn_service import get_top
    try:
        stories = await get_top(n=5)
        for s in stories:
            await enqueue("process_inbound_message", {
                "platform": "hn", "message_id": s.get("url", s["title"]),
                "thread_id": None, "sender_id": s.get("by", "hn"),
                "sender_name": f"HN ({s.get('by', '')})",
                "content": f"{s['title']} (⬆{s['score']})\n{s.get('url', '')}",
                "raw": s, "received_at": __import__("datetime").datetime.utcnow().isoformat(),
            })
    except Exception as exc:
        log.error("hn_poll_error", error=str(exc))

async def poll_github(ctx: dict) -> None:
    """Poll GitHub notifications."""
    from api.services.github_service import get_notifications
    try:
        notifs = await get_notifications()
        for n in notifs:
            await enqueue("process_inbound_message", {
                "platform": "github", "message_id": n.get("url", n["title"]),
                "thread_id": n.get("repo"), "sender_id": "github",
                "sender_name": f"GitHub ({n.get('repo', '')})",
                "content": f"[{n['type']}] {n['title']} — {n.get('reason', '')}",
                "raw": n, "received_at": __import__("datetime").datetime.utcnow().isoformat(),
            })
    except Exception as exc:
        log.error("github_poll_error", error=str(exc))

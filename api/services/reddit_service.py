"""
Reddit service — poll subreddits via JSON API (no auth needed).
"""

from __future__ import annotations

import httpx
from api.core.logging import log
from api.core.queue import get_redis

REDDIT_BASE = "https://www.reddit.com"
USER_AGENT = "ARIA/1.0 personal automation bot"


async def poll_subreddit(subreddit: str, keywords: list[str] | None = None, limit: int = 10) -> list[dict]:
    """Fetch new posts from a subreddit. Dedup via Redis. Optionally filter by keywords."""
    try:
        redis = await get_redis()
        seen_key = f"reddit_seen:{subreddit}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{REDDIT_BASE}/r/{subreddit}/new.json", params={"limit": limit}, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            data = resp.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            post_id = post.get("id", "")
            if not post_id:
                continue
            if await redis.sismember(seen_key, post_id):
                continue
            await redis.sadd(seen_key, post_id)
            await redis.expire(seen_key, 604800)
            title = post.get("title", "")
            selftext = post.get("selftext", "")[:500]
            if keywords:
                combined = f"{title} {selftext}".lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            posts.append({"id": post_id, "title": title, "url": f"https://reddit.com{post.get('permalink', '')}", "score": post.get("score", 0), "author": post.get("author", ""), "selftext": selftext, "subreddit": subreddit})
        log.info("reddit_polled", subreddit=subreddit, new_count=len(posts))
        return posts
    except Exception as exc:
        log.error("reddit_poll_failed", error=str(exc), subreddit=subreddit)
        return []

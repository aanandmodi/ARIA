"""
HackerNews service — Firebase API (no auth).
"""
from __future__ import annotations
import httpx
from api.core.logging import log

HN_API = "https://hacker-news.firebaseio.com/v0"

async def get_top(n: int = 5) -> list[dict]:
    """Fetch top n HN stories."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{HN_API}/topstories.json")
            resp.raise_for_status()
            ids = resp.json()[:n]
            stories = []
            for sid in ids:
                r = await client.get(f"{HN_API}/item/{sid}.json")
                if r.status_code == 200:
                    item = r.json()
                    stories.append({"title": item.get("title",""), "url": item.get("url",""), "score": item.get("score",0), "by": item.get("by",""), "descendants": item.get("descendants",0)})
            return stories
    except Exception as exc:
        log.error("hn_fetch_failed", error=str(exc))
        return []

def format_stories(stories: list[dict]) -> str:
    if not stories:
        return "No HN stories."
    lines = []
    for i, s in enumerate(stories, 1):
        lines.append(f"{i}. {s['title']} (⬆{s['score']}) — {s.get('url','')}")
    return "\n".join(lines)

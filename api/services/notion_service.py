"""
Notion service — create notes, tasks, search.
"""

from __future__ import annotations

import asyncio
from functools import partial

from notion_client import Client

from api.core.config import settings
from api.core.logging import log

_client: Client | None = None


def _get_client() -> Client | None:
    global _client
    if not settings.notion_token:
        return None
    if _client is None:
        _client = Client(auth=settings.notion_token)
    return _client


async def create_note(
    title: str,
    content: str,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Create a page in the Notion notes database. Returns page ID."""
    client = _get_client()
    if client is None or not settings.notion_notes_db_id:
        log.warning("notion_not_configured")
        return ""
    try:
        properties: dict = {
            "Name": {"title": [{"text": {"content": title or "Untitled"}}]},
        }
        if tags:
            properties["Tags"] = {"multi_select": [{"name": t} for t in tags]}
        if source_url:
            properties["URL"] = {"url": source_url}

        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                },
            }
        ]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                client.pages.create,
                parent={"database_id": settings.notion_notes_db_id},
                properties=properties,
                children=children,
            ),
        )
        page_id = result.get("id", "")
        log.info("notion_note_created", page_id=page_id, title=title)
        return page_id
    except Exception as exc:
        log.error("notion_note_failed", error=str(exc))
        return ""


async def create_task(title: str, due: str | None = None) -> str:
    """Create a task page in the Notion tasks database."""
    client = _get_client()
    if client is None or not settings.notion_tasks_db_id:
        log.warning("notion_tasks_not_configured")
        return ""
    try:
        properties: dict = {
            "Name": {"title": [{"text": {"content": title}}]},
        }
        if due:
            properties["Due"] = {"date": {"start": due}}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                client.pages.create,
                parent={"database_id": settings.notion_tasks_db_id},
                properties=properties,
            ),
        )
        page_id = result.get("id", "")
        log.info("notion_task_created", page_id=page_id, title=title)
        return page_id
    except Exception as exc:
        log.error("notion_task_failed", error=str(exc))
        return ""


async def search_notes(query: str) -> list[dict]:
    """Search Notion for pages matching query."""
    client = _get_client()
    if client is None:
        return []
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                client.search,
                query=query,
                filter={"property": "object", "value": "page"},
                page_size=10,
            ),
        )
        pages = []
        for page in result.get("results", []):
            title_prop = page.get("properties", {}).get("Name", {}).get("title", [])
            title = title_prop[0].get("text", {}).get("content", "Untitled") if title_prop else "Untitled"
            pages.append({
                "id": page.get("id", ""),
                "title": title,
                "url": page.get("url", ""),
                "created": page.get("created_time", ""),
            })
        return pages
    except Exception as exc:
        log.error("notion_search_failed", error=str(exc))
        return []

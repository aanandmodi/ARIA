"""
Slack service — send messages via Slack SDK.
"""

from __future__ import annotations

import asyncio
from functools import partial

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from api.core.config import settings
from api.core.logging import log

_client: WebClient | None = None


def _get_client() -> WebClient | None:
    global _client
    if not settings.slack_bot_token:
        return None
    if _client is None:
        _client = WebClient(token=settings.slack_bot_token)
    return _client


async def send_message(channel: str, text: str) -> bool:
    """Send a message to a Slack channel."""
    client = _get_client()
    if client is None:
        log.warning("slack_not_configured")
        return False
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(client.chat_postMessage, channel=channel, text=text),
        )
        log.info("slack_sent", channel=channel, length=len(text))
        return True
    except SlackApiError as exc:
        log.error("slack_send_failed", error=str(exc), channel=channel)
        return False
    except Exception as exc:
        log.error("slack_send_error", error=str(exc), channel=channel)
        return False

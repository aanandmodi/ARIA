"""
Slack webhook route — Events API handler.
"""
from __future__ import annotations
from fastapi import APIRouter, Request, Response
from api.adapters.slack_adapter import parse as slack_parse
from api.core.logging import log
from api.core.queue import enqueue

router = APIRouter()

@router.post("/slack")
async def slack_webhook(request: Request) -> Response:
    """Handle Slack Events API requests (including URL verification)."""
    try:
        body = await request.json()
        # URL verification challenge
        if body.get("type") == "url_verification":
            return Response(content=body.get("challenge",""), media_type="text/plain")
        if body.get("type") == "event_callback":
            msg = slack_parse(body)
            if msg:
                await enqueue("process_inbound_message", msg.to_dict())
        return Response(status_code=200)
    except Exception as exc:
        log.error("slack_webhook_error", error=str(exc))
        return Response(status_code=200)

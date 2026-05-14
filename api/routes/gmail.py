"""
Gmail webhook route — receives Pub/Sub push notifications.
"""
from __future__ import annotations
import base64, json
from fastapi import APIRouter, Request, Response
from api.adapters.gmail_adapter import parse as gmail_parse
from api.core.logging import log
from api.core.queue import enqueue

router = APIRouter()

@router.post("/gmail")
async def gmail_webhook(request: Request) -> Response:
    """Receive Gmail Pub/Sub push notification."""
    try:
        body = await request.json()
        message = body.get("message", {})
        data = message.get("data", "")
        if data:
            decoded = json.loads(base64.b64decode(data).decode("utf-8"))
            log.info("gmail_push_received", email=decoded.get("emailAddress",""), history_id=decoded.get("historyId",""))
            msg = gmail_parse(decoded)
            if msg:
                await enqueue("process_inbound_message", msg.to_dict())
        return Response(status_code=200)
    except Exception as exc:
        log.error("gmail_webhook_error", error=str(exc))
        return Response(status_code=200)

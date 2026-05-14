"""
Internal routes — WhatsApp inbound from Baileys container.
"""
from __future__ import annotations
from fastapi import APIRouter, Request, Response
from api.adapters.whatsapp_adapter import parse as wa_parse
from api.core.logging import log
from api.core.queue import enqueue

router = APIRouter()

@router.post("/whatsapp/inbound")
async def whatsapp_inbound(request: Request) -> Response:
    """Receive inbound WhatsApp messages from Baileys container."""
    try:
        body = await request.json()
        log.info("whatsapp_inbound_received", jid=body.get("jid",""))
        msg = wa_parse(body)
        if msg:
            await enqueue("process_inbound_message", msg.to_dict())
        return Response(status_code=200)
    except Exception as exc:
        log.error("whatsapp_inbound_error", error=str(exc))
        return Response(status_code=200)

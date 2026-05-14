"""
SMS Webhook Route (e.g. Twilio).
"""
import uuid
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import PlainTextResponse
from api.core.logging import log
from api.core.queue import enqueue

router = APIRouter()

@router.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
):
    """Receive inbound SMS from Twilio."""
    log.info("sms_webhook_received", sender=From, msg_id=MessageSid)

    # Format for inbound processor
    inbound_payload = {
        "platform": "sms",
        "message_id": MessageSid,
        "thread_id": From,
        "sender_id": From,
        "sender_name": From,
        "content": Body,
        "raw": {"From": From, "Body": Body, "MessageSid": MessageSid},
    }

    # Queue for processing
    await enqueue("process_inbound_message", inbound_payload)

    # Twilio expects a TwiML response. An empty Response tag is enough to ack.
    twiml = "<Response></Response>"
    return PlainTextResponse(content=twiml, media_type="application/xml")

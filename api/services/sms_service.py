"""
SMS service — send/receive via Android SMS Gateway REST API.
"""

from __future__ import annotations

import httpx

from api.core.config import settings
from api.core.logging import log


async def send_sms(phone: str, text: str) -> bool:
    """Send an SMS via the Android SMS Gateway."""
    if not settings.sms_gateway_url or not settings.sms_gateway_token:
        log.warning("sms_not_configured")
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.sms_gateway_url}/message",
                headers={"Authorization": f"Bearer {settings.sms_gateway_token}"},
                json={
                    "phoneNumbers": [phone],
                    "message": text,
                },
            )
            resp.raise_for_status()
            log.info("sms_sent", phone=phone, length=len(text))
            return True
    except Exception as exc:
        log.error("sms_send_failed", error=str(exc), phone=phone)
        return False

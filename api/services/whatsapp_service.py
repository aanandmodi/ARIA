"""
WhatsApp service — send messages via Baileys REST API.
"""

from __future__ import annotations

import httpx

from api.core.config import settings
from api.core.logging import log


async def send_message(jid: str, text: str) -> bool:
    """Send a text message to a WhatsApp JID via Baileys."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.baileys_url}/send",
                json={"jid": jid, "text": text},
            )
            resp.raise_for_status()
            log.info("whatsapp_sent", jid=jid, length=len(text))
            return True
    except Exception as exc:
        log.error("whatsapp_send_failed", error=str(exc), jid=jid)
        return False


async def send_media(
    jid: str,
    file_url: str,
    mimetype: str,
    caption: str = "",
) -> bool:
    """Send a media file (image/document) to a WhatsApp JID."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.baileys_url}/send-media",
                json={
                    "jid": jid,
                    "url": file_url,
                    "mimetype": mimetype,
                    "caption": caption,
                },
            )
            resp.raise_for_status()
            log.info("whatsapp_media_sent", jid=jid, mimetype=mimetype)
            return True
    except Exception as exc:
        log.error("whatsapp_media_failed", error=str(exc), jid=jid)
        return False


async def fetch_history(jid: str, limit: int = 50) -> list[dict]:
    """Fetch recent message history for a JID from Baileys store."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.baileys_url}/messages",
                params={"jid": jid, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("messages", [])
    except Exception as exc:
        log.error("whatsapp_history_failed", error=str(exc), jid=jid)
        return []


async def search_history(query: str, limit: int = 10) -> list[dict]:
    """Search global message history from Baileys store."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.baileys_url}/search",
                params={"q": query, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
    except Exception as exc:
        log.error("whatsapp_search_failed", error=str(exc), query=query)
        return []


async def get_contacts() -> list[dict]:
    """Get WhatsApp contacts."""
    from api.core.cache import cached
    
    @cached("contacts_whatsapp", ttl=3600)
    async def _fetch_contacts():
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{settings.baileys_url}/contacts")
                resp.raise_for_status()
                data = resp.json()
                
                contacts = []
                for c in data.get("contacts", []):
                    contacts.append({
                        "name": c.get("name", c.get("phone", "")),
                        "phone": c.get("phone", ""),
                        "jid": c.get("jid", ""),
                        "platform": "whatsapp"
                    })
                
                log.info("whatsapp_contacts_fetched", count=len(contacts))
                return contacts
        except Exception as exc:
            log.error("whatsapp_contacts_failed", error=str(exc))
            return []
    
    return await _fetch_contacts()


async def search_messages(query: str, limit: int = 10) -> list[dict]:
    """Search WhatsApp messages."""
    try:
        results = await search_history(query, limit)
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "contact": r.get("pushName", r.get("jid", "")),
                "preview": r.get("message", {}).get("conversation", "")[:100],
                "timestamp": r.get("messageTimestamp", ""),
                "jid": r.get("jid", "")
            })
        
        log.info("whatsapp_search_complete", query=query, results=len(formatted_results))
        return formatted_results
    except Exception as exc:
        log.error("whatsapp_search_failed", error=str(exc), query=query)
        return []


async def get_chat_context(jid: str) -> dict:
    """Get context about a WhatsApp chat (group vs personal, participants, etc.)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.baileys_url}/chat-info",
                params={"jid": jid}
            )
            resp.raise_for_status()
            data = resp.json()
            
            is_group = jid.endswith("@g.us")
            
            return {
                "is_group": is_group,
                "participants": data.get("participants", []) if is_group else [],
                "name": data.get("name", ""),
                "jid": jid
            }
    except Exception as exc:
        log.error("whatsapp_chat_context_failed", error=str(exc), jid=jid)
        return {
            "is_group": jid.endswith("@g.us"),
            "participants": [],
            "name": "",
            "jid": jid
        }

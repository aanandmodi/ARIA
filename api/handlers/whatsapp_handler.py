"""
WhatsApp handler — resolving contacts and sending outbound WhatsApp messages.
"""
from __future__ import annotations
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, whatsapp_service
from api.db.models import Contact
from api.core.logging import log

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    contact_name = params.get("contact_name")
    phone = params.get("phone")
    message = params.get("message")

    if not message:
        await telegram_service.send_message("❌ Please specify the message to send.")
        return

    jid = None
    resolved_name = None

    if phone:
        clean_phone = "".join(c for c in str(phone) if c.isdigit())
        jid = f"{clean_phone}@s.whatsapp.net"
        resolved_name = phone
    elif contact_name:
        # Search DB for name/group name
        stmt = select(Contact).where(
            or_(
                Contact.name.ilike(f"%{contact_name}%"),
                Contact.nickname.ilike(f"%{contact_name}%")
            )
        )
        result = await db.execute(stmt)
        contacts = result.scalars().all()
        
        if not contacts:
            await telegram_service.send_message(f"❌ Could not find any contact or group matching '<b>{contact_name}</b>' on WhatsApp.")
            return
            
        # Select best match
        best_match = None
        for c in contacts:
            if c.name and c.name.lower() == contact_name.lower():
                best_match = c
                break
            if c.nickname and c.nickname.lower() == contact_name.lower():
                best_match = c
                break
                
        if not best_match:
            best_match = contacts[0]
            
        c = best_match
        if c.is_group:
            jid = c.group_jid
        else:
            jid = c.platform_ids.get("whatsapp") if c.platform_ids else None
            if not jid and c.phone:
                jid = f"{c.phone}@s.whatsapp.net"
                
        resolved_name = c.name

    if jid and "@" not in jid:
        if "-" in jid or len(jid) > 15:
            jid = f"{jid}@g.us"
        elif len(jid) in (13, 14, 15):
            jid = f"{jid}@lid"
        else:
            jid = f"{jid}@s.whatsapp.net"

    if not jid:
        await telegram_service.send_message(f"❌ Could not resolve phone number or JID for '<b>{contact_name}</b>'.")
        return

    platform_desc = "group chat" if jid.endswith("@g.us") else "contact"
    await telegram_service.send_message(f"📤 Sending WhatsApp to {platform_desc} <b>{resolved_name}</b>...")

    success = await whatsapp_service.send_message(jid, message)
    if success:
        await telegram_service.send_message(f"✅ WhatsApp sent successfully to <b>{resolved_name}</b>!\n\n<i>{message}</i>")
    else:
        await telegram_service.send_message(f"❌ Failed to send WhatsApp message to {resolved_name}.")

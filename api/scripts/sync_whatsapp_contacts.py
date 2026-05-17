"""
Script to synchronize all WhatsApp contacts and groups from Baileys to PostgreSQL contacts table.
"""
import asyncio
import httpx
from sqlalchemy import select
from api.db.session import async_session_factory
from api.db.models import Contact
from api.core.logging import log

async def sync():
    print("Fetching contacts from Baileys...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get("http://baileys:3001/contacts")
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"Error fetching contacts from Baileys: {e}")
        return

    contacts = data.get("contacts", [])
    print(f"Fetched {len(contacts)} contacts/groups from WhatsApp.")

    async with async_session_factory() as db:
        added_count = 0
        updated_count = 0
        for c in contacts:
            jid = c.get("jid", "")
            name = c.get("name", "")
            phone = c.get("phone", "")
            is_group = c.get("isGroup", False)

            if not jid:
                continue

            # Check if contact exists
            if is_group:
                stmt = select(Contact).where(Contact.group_jid == jid)
            else:
                stmt = select(Contact).where(Contact.phone == phone)
            
            result = await db.execute(stmt)
            contact = result.scalar_one_or_none()

            platform_ids = {"whatsapp": jid}

            if not contact:
                # Create contact
                contact = Contact(
                    name=name,
                    phone=phone if not is_group else None,
                    is_group=is_group,
                    group_jid=jid if is_group else None,
                    platform_ids=platform_ids,
                )
                db.add(contact)
                added_count += 1
            else:
                # Update contact
                contact.name = name
                contact.is_group = is_group
                if is_group:
                    contact.group_jid = jid
                else:
                    contact.phone = phone
                
                # Merge platform_ids
                p_ids = dict(contact.platform_ids or {})
                p_ids["whatsapp"] = jid
                contact.platform_ids = p_ids
                updated_count += 1
            
        await db.commit()
        print(f"Sync complete! Added: {added_count}, Updated: {updated_count} contacts/groups.")

if __name__ == "__main__":
    asyncio.run(sync())

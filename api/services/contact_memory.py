"""
Contact memory system - learns and remembers contact names and preferences.
"""
from __future__ import annotations

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fuzzywuzzy import fuzz

from api.core.logging import log
from api.db.models import Contact, Memory


async def learn_contact_name(
    identifier: str,  # phone/email
    name: str,
    platform: str,
    db: AsyncSession
) -> Contact:
    """
    Learn and store contact name.
    
    Args:
        identifier: Phone number or email address
        name: Contact's name
        platform: Platform where contact was found
        db: Database session
    
    Returns:
        Contact object
    """
    # Check if contact exists
    result = await db.execute(
        select(Contact).where(
            or_(
                Contact.email == identifier,
                Contact.phone == identifier
            )
        )
    )
    contact = result.scalar_one_or_none()
    
    if contact:
        # Update name if different and more complete
        if name and (not contact.name or len(name) > len(contact.name)):
            old_name = contact.name
            contact.name = name
            log.info("contact_name_updated", old=old_name, new=name, identifier=identifier)
        
        # Update platform IDs
        platform_ids = contact.platform_ids or {}
        platform_ids[platform] = identifier
        contact.platform_ids = platform_ids
        
        await db.flush()
    else:
        # Create new contact
        contact = Contact(
            name=name,
            email=identifier if "@" in identifier else None,
            phone=identifier if "@" not in identifier else None,
            platform_ids={platform: identifier},
            message_count=0
        )
        db.add(contact)
        await db.flush()
        log.info("contact_created", name=name, identifier=identifier, platform=platform)
    
    return contact


async def resolve_contact_name(
    name: str,
    db: AsyncSession,
    platform: str | None = None
) -> Contact | None:
    """
    Resolve a name to a contact using fuzzy matching.
    
    Args:
        name: Name to search for
        db: Database session
        platform: Optional platform filter
    
    Returns:
        Best matching Contact or None
    """
    # Exact match first (case-insensitive)
    result = await db.execute(
        select(Contact).where(
            Contact.name.ilike(f"%{name}%")
        )
    )
    contacts = result.scalars().all()
    
    if not contacts:
        log.info("contact_not_found", name=name)
        return None
    
    # If only one match, return it
    if len(contacts) == 1:
        log.info("contact_resolved", name=name, found=contacts[0].name)
        return contacts[0]
    
    # Multiple matches - use fuzzy matching to find best match
    best_match = None
    best_score = 0
    
    for contact in contacts:
        if not contact.name:
            continue
        
        # Calculate fuzzy match score
        score = fuzz.ratio(name.lower(), contact.name.lower())
        
        # Boost score if platform matches
        if platform and contact.platform_ids and platform in contact.platform_ids:
            score += 10
        
        if score > best_score:
            best_score = score
            best_match = contact
    
    if best_match and best_score >= 70:  # Threshold for acceptable match
        log.info("contact_resolved_fuzzy", name=name, found=best_match.name, score=best_score)
        return best_match
    
    log.info("contact_no_good_match", name=name, best_score=best_score)
    return None


async def get_contact_identifier(
    contact: Contact,
    platform: str
) -> str | None:
    """
    Get the identifier (phone/email) for a contact on a specific platform.
    
    Args:
        contact: Contact object
        platform: Platform name
    
    Returns:
        Identifier string or None
    """
    # Check platform_ids first
    if contact.platform_ids and platform in contact.platform_ids:
        return contact.platform_ids[platform]
    
    # Fall back to email/phone based on platform
    if platform in ("gmail", "email"):
        return contact.email
    elif platform in ("whatsapp", "sms"):
        return contact.phone
    
    # Return any available identifier
    return contact.email or contact.phone


async def store_contact_preference(
    contact_id: str,
    preference_type: str,
    preference_value: str,
    db: AsyncSession
) -> None:
    """
    Store a preference about a contact.
    
    Args:
        contact_id: Contact UUID
        preference_type: Type of preference (e.g., "communication_method", "timezone")
        preference_value: Value of the preference
        db: Database session
    """
    memory = Memory(
        entity_type="contact_preference",
        entity_key=contact_id,
        fact=f"{preference_type}: {preference_value}",
        confidence=1.0,
        source="explicit"
    )
    db.add(memory)
    await db.flush()
    
    log.info("contact_preference_stored", 
             contact_id=contact_id, 
             type=preference_type, 
             value=preference_value)


async def get_contact_preferences(
    contact_id: str,
    db: AsyncSession
) -> dict[str, str]:
    """
    Get all stored preferences for a contact.
    
    Args:
        contact_id: Contact UUID
        db: Database session
    
    Returns:
        Dict of preference_type -> preference_value
    """
    result = await db.execute(
        select(Memory).where(
            Memory.entity_type == "contact_preference",
            Memory.entity_key == contact_id
        )
    )
    memories = result.scalars().all()
    
    preferences = {}
    for memory in memories:
        # Parse "type: value" format
        if ": " in memory.fact:
            pref_type, pref_value = memory.fact.split(": ", 1)
            preferences[pref_type] = pref_value
    
    return preferences


async def search_contacts(
    query: str,
    db: AsyncSession,
    limit: int = 10
) -> list[Contact]:
    """
    Search contacts by name, email, or phone.
    
    Args:
        query: Search query
        db: Database session
        limit: Maximum results
    
    Returns:
        List of matching contacts
    """
    result = await db.execute(
        select(Contact).where(
            or_(
                Contact.name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%"),
                Contact.phone.ilike(f"%{query}%")
            )
        ).limit(limit)
    )
    
    contacts = result.scalars().all()
    log.info("contacts_searched", query=query, results=len(contacts))
    
    return contacts

# Made with Bob

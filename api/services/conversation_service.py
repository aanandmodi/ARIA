import asyncio
import logging
import os
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc

from api.db.models import ConversationTurn, Contact
from groq import AsyncGroq

import uuid

logger = logging.getLogger(__name__)

async def append_turn(db: AsyncSession, contact_id: uuid.UUID, role: str, content: str) -> ConversationTurn:
    """
    Append a new conversation turn to the database.
    role: 'user', 'assistant', 'system'
    """
    turn = ConversationTurn(
        contact_id=contact_id,
        role=role,
        content=content
    )
    db.add(turn)
    await db.flush()
    await db.refresh(turn)
    return turn

async def get_recent_history(db: AsyncSession, contact_id: uuid.UUID, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get the most recent conversation history for a contact.
    Returned format is suitable for LLM APIs: [{"role": "user", "content": "..."}]
    """
    stmt = (
        select(ConversationTurn)
        .where(ConversationTurn.contact_id == contact_id)
        .order_by(ConversationTurn.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    results = result.scalars().all()
    
    # Reverse to get chronological order (oldest first)
    history = [
        {"role": turn.role, "content": turn.content}
        for turn in reversed(results)
    ]
    return history

async def _summarize_turns(turns: List[ConversationTurn]) -> str:
    """Use Groq to summarize a list of conversation turns."""
    try:
        client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        
        conversation_text = "\n".join([f"{t.role.capitalize()}: {t.content}" for t in turns])
        
        prompt = (
            "Summarize the following conversation history concisely. "
            "Retain the key facts, user intents, and important context. "
            "Respond ONLY with the summary.\n\n"
            f"{conversation_text}"
        )
        
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Or whatever default model ARIA uses
            messages=[
                {"role": "system", "content": "You are a concise conversation summarizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=512
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error summarizing turns: {e}")
        return "Conversation summary failed."

async def maybe_compress(db: AsyncSession, contact_id: uuid.UUID, threshold: int = 20, compress_count: int = 15):
    """
    If a contact has more than `threshold` turns, summarize the oldest `compress_count` turns 
    into a single 'system' summary turn to save context window.
    """
    # Count total turns
    count_stmt = select(func.count()).select_from(ConversationTurn).where(ConversationTurn.contact_id == contact_id)
    result = await db.execute(count_stmt)
    total_turns = result.scalar()
    
    if total_turns and total_turns > threshold:
        logger.info(f"Compressing {compress_count} turns for contact {contact_id} (total: {total_turns})")
        
        # Get oldest `compress_count` turns
        oldest_stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.contact_id == contact_id)
            .order_by(ConversationTurn.created_at.asc())
            .limit(compress_count)
        )
        result = await db.execute(oldest_stmt)
        oldest_turns = list(result.scalars().all())
        
        if not oldest_turns:
            return
            
        # Summarize
        summary_text = await _summarize_turns(oldest_turns)
        
        # Delete old turns
        for turn in oldest_turns:
            await db.delete(turn)
            
        # Insert summary turn
        summary_turn = ConversationTurn(
            contact_id=contact_id,
            role="system",
            content=f"[Summary of previous conversation]: {summary_text}"
        )
        
        summary_turn.created_at = oldest_turns[-1].created_at 
        
        db.add(summary_turn)
        await db.flush()
        logger.info(f"Compression complete for contact {contact_id}.")


"""
Unified cross-platform search service.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.models import Message
from api.core.logging import log

async def universal_search(db: AsyncSession, query: str, platform: str = "all", days: int | None = None) -> list[dict]:
    """Full-text search across messages table using PostgreSQL."""
    try:
        stmt = select(Message).order_by(Message.created_at.desc()).limit(20)
        
        if query:
            stmt = stmt.where(
                text("to_tsvector('english', content) @@ websearch_to_tsquery('english', :q)")
            ).params(q=query)
            
        if platform != "all":
            stmt = stmt.where(Message.platform == platform)
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            stmt = stmt.where(Message.created_at >= cutoff)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        return [{"platform": m.platform, "sender_name": m.sender_name, "summary": m.summary or "", "content": m.content[:1000] if m.content else "", "date": m.created_at.isoformat(), "message_id": str(m.id)} for m in messages]
    except Exception as exc:
        log.error("search_failed", error=str(exc), query=query)
        return []

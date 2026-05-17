"""
Rolling conversation history in Redis.
Every Telegram exchange is stored here and injected into every Groq call.
This is why the bot will finally understand context.
"""
from __future__ import annotations

import json
from datetime import datetime

from redis.asyncio import Redis

from api.core.logging import log
from api.llm.client import groq_client

CONV_KEY = "aria:conv"
SUMMARY_KEY = "aria:conv_summary"
MAX_TURNS = 15  # 15 exchanges = 30 redis entries (user + assistant)


async def append_turn(
    redis: Redis,
    role: str,
    content: str,
    intent: str = "",
) -> None:
    """
    Append a conversation turn to Redis.
    
    Args:
        redis: Redis connection
        role: "user" or "assistant"
        content: The message content
        intent: Optional intent classification
    """
    turn = json.dumps({
        "role": role,
        "content": content,
        "intent": intent,
        "ts": datetime.utcnow().isoformat(),
    })
    
    await redis.rpush(CONV_KEY, turn)
    
    # Keep only the last MAX_TURNS * 2 entries (user + assistant pairs)
    await redis.ltrim(CONV_KEY, -(MAX_TURNS * 2), -1)
    
    # Set TTL to 2 hours
    await redis.expire(CONV_KEY, 7200)


async def get_history(redis: Redis) -> list[dict]:
    """
    Get conversation history formatted for Groq.
    
    Returns:
        List of {"role": "user"|"assistant", "content": str} dicts
    """
    try:
        raw = await redis.lrange(CONV_KEY, 0, -1)
        history = []
        
        for item in raw:
            try:
                parsed = json.loads(item)
                history.append({
                    "role": parsed["role"],
                    "content": parsed["content"]
                })
            except (json.JSONDecodeError, KeyError):
                continue
                
        return history
    except Exception as exc:
        log.error("get_history_failed", error=str(exc))
        return []


async def get_summary(redis: Redis) -> str:
    """
    Get the compressed summary of older conversation turns.
    
    Returns:
        Summary text or empty string
    """
    try:
        summary_bytes = await redis.get(SUMMARY_KEY)
        return summary_bytes.decode() if summary_bytes else ""
    except Exception:
        return ""


async def maybe_compress(redis: Redis) -> None:
    """
    When history gets long, summarize old turns and start fresh.
    
    This prevents context window overflow while maintaining continuity.
    """
    try:
        raw = await redis.lrange(CONV_KEY, 0, -1)
        
        # Only compress if we have more than MAX_TURNS * 2 entries
        if len(raw) < MAX_TURNS * 2:
            return
            
        # Take the first 20 turns to summarize
        to_summarize = raw[:20]
        
        text_lines = []
        for item in to_summarize:
            try:
                parsed = json.loads(item)
                role = parsed["role"].upper()
                content = parsed["content"]
                text_lines.append(f"{role}: {content}")
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not text_lines:
            return
            
        text = "\n".join(text_lines)
        
        # Ask Groq to summarize
        summary = await groq_client.chat(
            f"Summarize this conversation in 4 concise sentences. "
            f"Preserve: names, facts, decisions, context.\n\n{text}",
            max_tokens=200,
            temperature=0.3,
        )
        
        # Store summary
        await redis.set(SUMMARY_KEY, summary, ex=86400)  # 24h TTL
        
        # Clear old history (keep only recent turns)
        await redis.delete(CONV_KEY)
        
        log.info("conversation_compressed", summary_length=len(summary))
        
    except Exception as exc:
        log.error("maybe_compress_failed", error=str(exc))


async def clear_history(redis: Redis) -> None:
    """Clear all conversation history and summary."""
    try:
        await redis.delete(CONV_KEY)
        await redis.delete(SUMMARY_KEY)
        log.info("conversation_history_cleared")
    except Exception as exc:
        log.error("clear_history_failed", error=str(exc))

# Made with Bob

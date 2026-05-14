"""
Summarisation via Groq LLM.
"""

from __future__ import annotations

from api.core.logging import log
from api.llm.client import chat
from api.llm.prompts import SUMMARISE_PROMPT, SUMMARISE_SYSTEM


async def summarise(text: str, context_type: str = "message") -> str:
    """
    Summarise arbitrary text in 1-3 sentences.
    Returns truncated text as fallback.
    """
    try:
        prompt = SUMMARISE_PROMPT.format(
            context_type=context_type,
            text=text[:4000],
        )
        result = await chat(prompt, system=SUMMARISE_SYSTEM, max_tokens=256)
        return result.strip() if result.strip() else text[:200]
    except Exception as exc:
        log.error("summarise_failed", error=str(exc))
        return text[:200] + ("..." if len(text) > 200 else "")

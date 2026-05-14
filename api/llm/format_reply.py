"""
Format outbound replies for each platform using Groq.
"""

from __future__ import annotations

from api.core.logging import log
from api.llm.client import chat
from api.llm.prompts import FORMAT_REPLY_PROMPT, FORMAT_REPLY_SYSTEM


async def format_reply(
    reply_text: str,
    platform: str,
    contact_name: str = "Unknown",
    context: str = "",
) -> str:
    """
    Reformat a user's short reply into a polished message appropriate
    for the target platform. Returns the original text on error.
    """
    try:
        prompt = FORMAT_REPLY_PROMPT.format(
            platform=platform,
            contact_name=contact_name,
            context=context[:1500] if context else "No prior context available.",
            reply=reply_text,
        )
        result = await chat(prompt, system=FORMAT_REPLY_SYSTEM, max_tokens=512)
        return result.strip() if result.strip() else reply_text
    except Exception as exc:
        log.error("format_reply_failed", error=str(exc), platform=platform)
        return reply_text

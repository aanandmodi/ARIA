"""
Groq async client wrapper with retry logic and rate-limit awareness.
"""

from __future__ import annotations

import asyncio
import json
import re
import time

from groq import AsyncGroq, RateLimitError

from api.core.config import settings
from api.core.logging import log

_client: AsyncGroq | None = None

# Simple in-memory rate-limit tracker
_request_timestamps: list[float] = []
_MAX_RPM = 25  # conservative limit for Groq free tier


def get_groq_client() -> AsyncGroq:
    """Return (and lazily create) the async Groq client."""
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


async def _rate_limit_delay() -> None:
    """If we are approaching the rate limit, sleep briefly."""
    now = time.time()
    # Remove timestamps older than 60s
    cutoff = now - 60
    while _request_timestamps and _request_timestamps[0] < cutoff:
        _request_timestamps.pop(0)

    if len(_request_timestamps) >= _MAX_RPM - 2:
        wait = 60 - (now - _request_timestamps[0]) + 1
        if wait > 0:
            log.warning("groq_rate_limit_preemptive_wait", wait_seconds=round(wait, 1))
            await asyncio.sleep(wait)


async def chat(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """
    Send a chat completion to Groq with automatic retry on rate-limit errors.
    Returns the assistant's response text.
    """
    client = get_groq_client()
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            await _rate_limit_delay()
            start = time.time()

            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            _request_timestamps.append(time.time())
            elapsed = round(time.time() - start, 2)
            usage = response.usage
            log.info(
                "groq_chat",
                tokens_in=usage.prompt_tokens if usage else 0,
                tokens_out=usage.completion_tokens if usage else 0,
                latency_s=elapsed,
                attempt=attempt + 1,
            )
            return response.choices[0].message.content or ""

        except RateLimitError as exc:
            last_error = exc
            wait = (2 ** attempt) * 2  # 2, 4, 8 seconds
            log.warning("groq_rate_limited", attempt=attempt + 1, wait=wait)
            await asyncio.sleep(wait)

        except Exception as exc:
            last_error = exc
            wait = (2 ** attempt)
            log.error("groq_chat_error", error=str(exc), attempt=attempt + 1)
            await asyncio.sleep(wait)

    log.error("groq_chat_exhausted_retries", error=str(last_error))
    return ""


async def chat_json(
    prompt: str,
    system: str,
    max_tokens: int = 1024,
    temperature: float = 0.1,
) -> dict:
    """
    Chat completion that returns parsed JSON.
    Strips markdown fences and retries once with a stricter prompt on parse failure.
    """
    raw = await chat(prompt, system=system, max_tokens=max_tokens, temperature=temperature)

    for attempt in range(2):
        text = raw.strip()
        # Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt == 0:
                log.warning("groq_json_parse_retry", raw_preview=text[:200])
                raw = await chat(
                    f"Your previous response was not valid JSON. "
                    f"Return ONLY a valid JSON object, no markdown, no explanation.\n\n"
                    f"Original request:\n{prompt}",
                    system=system + "\nYou MUST respond with valid JSON only. No markdown fences.",
                    max_tokens=max_tokens,
                    temperature=0.0,
                )
            else:
                log.error("groq_json_parse_failed", raw_preview=text[:200])
                return {}

    return {}

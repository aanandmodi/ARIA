"""
Groq async client with proper retry, JSON parsing, and error handling.
This is the foundation for all LLM interactions in ARIA.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from groq import AsyncGroq

from api.core.config import settings
from api.core.logging import log


class GroqClient:
    """Async Groq client with retry logic and structured output support."""
    
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    async def chat(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 600,
        temperature: float = 0.7,
        retries: int = 3,
        model: str | None = None,
    ) -> str:
        """
        Send a chat completion request with retry logic.
        
        Args:
            prompt: User message
            system: System prompt (optional)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            retries: Number of retry attempts on failure
            model: Custom model name to use instead of default
            
        Returns:
            Response text from the model
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model or self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                log.warning("groq_chat_attempt_failed", 
                           attempt=attempt + 1, 
                           error=str(exc)[:100])
                if attempt == retries - 1:
                    log.error("groq_chat_failed", error=str(exc))
                    raise
                # Exponential backoff
                wait = 2 ** attempt
                await asyncio.sleep(wait)
        return ""

    async def chat_json(
        self,
        prompt: str,
        system: str | None = None,
        retries: int = 3,
        model: str | None = None,
        max_tokens: int = 800,
        temperature: float = 0.1,
    ) -> dict | list:
        """
        Chat that returns parsed JSON with aggressive cleanup.
        
        This method:
        1. Adds explicit JSON-only instructions to the system prompt
        2. Uses low temperature for deterministic output
        3. Strips markdown code fences
        4. Retries with stricter prompts on parse failures
        5. Returns empty dict/list as safe fallback
        
        Args:
            prompt: User message requesting structured output
            system: System prompt (will be enhanced with JSON instructions)
            retries: Number of retry attempts
            model: Custom model name to use instead of default
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON as dict or list, or {} on failure
        """
        enhanced_system = (system or "") + (
            "\n\nIMPORTANT: Return ONLY valid JSON. "
            "No markdown code fences. No explanatory text. "
            "Just raw JSON that can be parsed directly."
        )
        
        for attempt in range(retries):
            try:
                raw = await self.chat(
                    prompt=prompt,
                    system=enhanced_system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model,
                    retries=1,  # Retries are handled by the outer loop
                )
                
                # Aggressive cleanup of markdown fences
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
                cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
                cleaned = cleaned.strip()
                
                # Parse JSON
                parsed = json.loads(cleaned)
                return parsed
                
            except json.JSONDecodeError as exc:
                log.warning("groq_json_parse_failed",
                           attempt=attempt + 1,
                           error=str(exc)[:100],
                           raw_preview=raw[:200] if 'raw' in locals() else "N/A")
                
                if attempt == retries - 1:
                    log.error("groq_json_failed_all_attempts", raw=raw[:500])
                    return {}  # Safe fallback
                    
                # Make the prompt even more explicit on retry
                enhanced_system += "\n\nYour previous response was not valid JSON. Try again with ONLY JSON."
                await asyncio.sleep(1)
                
            except Exception as exc:
                log.error("groq_json_unexpected_error", error=str(exc))
                if attempt == retries - 1:
                    return {}
                await asyncio.sleep(2 ** attempt)
                
        return {}

    async def chat_with_history(
        self,
        system: str,
        history: list[dict],
        current_message: str,
        max_tokens: int = 800,
        temperature: float = 0.75,
    ) -> str:
        """
        Chat with full conversation history injected.
        
        This is the core method for conversational interactions where
        context from previous messages matters.
        
        Args:
            system: System prompt with personality/instructions
            history: List of {"role": "user"|"assistant", "content": str}
            current_message: The new user message
            max_tokens: Maximum response length
            temperature: Sampling temperature
            
        Returns:
            Assistant's response
        """
        messages = [{"role": "system", "content": system}]
        
        # Add conversation history (limit to last 12 turns to stay within context)
        messages.extend(history[-12:])
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            log.error("groq_chat_with_history_failed", error=str(exc))
            # Fallback: try without history if context is too long
            try:
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": current_message}
                ]
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception:
                return "I'm having trouble processing that right now. Please try again."


# Global instance
groq_client = GroqClient()


def get_groq_client() -> AsyncGroq:
    """Get the raw AsyncGroq client instance."""
    return groq_client.client


# Convenience functions for backward compatibility
async def chat(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 600,
    temperature: float = 0.7,
    model: str | None = None,
) -> str:
    """Convenience wrapper for groq_client.chat()"""
    return await groq_client.chat(prompt, system, max_tokens, temperature, model=model)


async def chat_json(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 800,
    temperature: float = 0.1,
    retries: int = 3,
) -> dict | list:
    """Convenience wrapper for groq_client.chat_json()"""
    return await groq_client.chat_json(
        prompt=prompt,
        system=system,
        retries=retries,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

# Made with Bob

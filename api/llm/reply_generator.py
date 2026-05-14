"""
Advanced Natural Reply Generator using Groq LLM.
Crafts context-aware, hyper-personalized replies based on the generated context and intent.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from groq import AsyncGroq
from api.core.logging import log
from api.db.models import UserProfile, Contact

async def generate_natural_reply(
    contact: Contact,
    user_profile: UserProfile,
    system_context: str,
    conversation_history: List[Dict[str, str]],
    latest_message: str,
    action_result: Optional[str] = None
) -> str:
    """
    Generate a natural, highly contextualized reply using the Groq LLM.
    
    Args:
        contact: The contact we are replying to.
        user_profile: The user's profile and preferences.
        system_context: The heavily enriched system prompt (from personal_context.py).
        conversation_history: List of {"role": "...", "content": "..."} turns.
        latest_message: The exact message the user just sent.
        action_result: Optional text containing the result of any backend actions (e.g., fetched emails, event created).
    """
    try:
        client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Build the messages array
        messages = [{"role": "system", "content": system_context}]
        
        # Add conversation history
        for turn in conversation_history:
            messages.append({"role": turn["role"], "content": turn["content"]})
            
        # Add the latest message
        messages.append({"role": "user", "content": latest_message})
        
        # If there's an action result to incorporate, inject it via a system message just before generating
        if action_result:
            action_injection = (
                f"[SYSTEM EVENT/RESULT]: {action_result}\n"
                "Acknowledge or use this result naturally in your reply."
            )
            messages.append({"role": "system", "content": action_injection})

        # Generate response
        response = await client.chat.completions.create(
            model="llama3-70b-8192",  # Adjust model as needed
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        
        reply_text = response.choices[0].message.content.strip()
        return reply_text
        
    except Exception as exc:
        log.error("reply_generation_failed", error=str(exc))
        return "I encountered an error trying to process that."

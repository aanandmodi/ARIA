"""
Quick Reply Service.
Generates smart, contextual quick reply options for incoming messages using LLM.
These options can be displayed as InlineKeyboard buttons on Telegram.
"""
import os
import json
from typing import List
from groq import AsyncGroq
from api.core.logging import log

async def generate_quick_replies(sender_name: str, message_content: str, max_options: int = 3) -> List[str]:
    """
    Generate short quick-reply options for a given inbound message.
    """
    try:
        client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        
        prompt = (
            f"Generate {max_options} short, natural, and distinct quick reply options "
            f"to respond to the following message from '{sender_name}'. "
            "Options should be 1-5 words max, conversational, and direct.\n\n"
            f"Message: {message_content}\n\n"
            'Return a JSON object with a single key "replies" containing an array of strings: {"replies": ["Option 1", ...]}'
        )
        
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You output only valid JSON objects."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=150
        )
        
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        
        if isinstance(parsed, dict) and "replies" in parsed:
            return [str(r) for r in parsed["replies"][:max_options]]
        elif isinstance(parsed, list):
            return [str(r) for r in parsed[:max_options]]
        elif isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    return [str(r) for r in v[:max_options]]
                    
        return ["Yes", "No", "Thanks"]
    except Exception as exc:
        log.error("quick_reply_generation_failed", error=str(exc))
        return ["Ok", "Got it"]


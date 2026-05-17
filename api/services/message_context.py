"""
Message context analysis service.
Detects group vs personal messages, urgency, participants, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from api.core.logging import log


@dataclass
class MessageContext:
    """Rich context about a message."""
    is_group: bool
    participants: list[str]
    urgency: str  # urgent/normal/low
    thread_id: str | None
    mentioned_users: list[str]
    platform: str
    sender_id: str
    
    def to_dict(self) -> dict:
        return {
            "is_group": self.is_group,
            "participants": self.participants,
            "urgency": self.urgency,
            "thread_id": self.thread_id,
            "mentioned_users": self.mentioned_users,
            "platform": self.platform,
            "sender_id": self.sender_id
        }


# Urgency keywords
URGENT_KEYWORDS = {
    "urgent", "asap", "emergency", "critical", "immediately", 
    "right now", "help", "sos", "911", "important"
}

LOW_PRIORITY_KEYWORDS = {
    "fyi", "whenever", "no rush", "when you can", "low priority"
}


def extract_mentions(content: str) -> list[str]:
    """Extract @mentions from message content."""
    if not content:
        return []
    
    # Match @username patterns
    mentions = re.findall(r'@(\w+)', content)
    return list(set(mentions))


def detect_urgency(content: str) -> str:
    """Detect message urgency from content."""
    if not content:
        return "normal"
    
    content_lower = content.lower()
    
    # Check for urgent keywords
    if any(keyword in content_lower for keyword in URGENT_KEYWORDS):
        return "urgent"
    
    # Check for low priority keywords
    if any(keyword in content_lower for keyword in LOW_PRIORITY_KEYWORDS):
        return "low"
    
    # Check for excessive punctuation (!!!, ???)
    if re.search(r'[!?]{3,}', content):
        return "urgent"
    
    # Check for ALL CAPS (at least 5 consecutive words)
    if re.search(r'\b[A-Z]{5,}\b.*\b[A-Z]{5,}\b', content):
        return "urgent"
    
    return "normal"


async def analyze_message_context(
    platform: str,
    message: dict,
    sender_id: str
) -> MessageContext:
    """
    Analyze message context for better routing and handling.
    
    Args:
        platform: Platform name (whatsapp, gmail, etc.)
        message: Raw message dict from platform
        sender_id: Sender identifier
    
    Returns:
        MessageContext with rich metadata
    """
    is_group = False
    participants = []
    thread_id = message.get("thread_id")
    content = message.get("content", "")
    
    # Platform-specific context extraction
    if platform == "whatsapp":
        # Check if group chat
        jid = message.get("jid", "")
        is_group = jid.endswith("@g.us")
        
        if is_group:
            # Get participants from message or fetch from service
            participants = message.get("participants", [])
            if not participants:
                # Fetch from WhatsApp service
                try:
                    from api.services.whatsapp_service import get_chat_context
                    context = await get_chat_context(jid)
                    participants = context.get("participants", [])
                except Exception:
                    pass
    
    elif platform == "gmail":
        # Check CC/BCC for group emails
        cc = message.get("cc", [])
        bcc = message.get("bcc", [])
        to = message.get("to", [])
        
        # If multiple recipients, consider it a group message
        all_recipients = []
        if isinstance(to, list):
            all_recipients.extend(to)
        elif to:
            all_recipients.append(to)
        
        all_recipients.extend(cc if isinstance(cc, list) else [cc] if cc else [])
        all_recipients.extend(bcc if isinstance(bcc, list) else [bcc] if bcc else [])
        
        is_group = len(all_recipients) > 1
        participants = all_recipients
        thread_id = message.get("threadId")
    
    elif platform == "discord":
        # Discord channels are always group contexts
        is_group = True
        participants = message.get("mentions", [])
    
    elif platform == "slack":
        # Slack channels are group, DMs are personal
        channel_type = message.get("channel_type", "")
        is_group = channel_type in ("channel", "group")
        participants = message.get("mentions", [])
    
    # Extract mentions and detect urgency
    mentioned_users = extract_mentions(content)
    urgency = detect_urgency(content)
    
    context = MessageContext(
        is_group=is_group,
        participants=participants,
        urgency=urgency,
        thread_id=thread_id,
        mentioned_users=mentioned_users,
        platform=platform,
        sender_id=sender_id
    )
    
    log.info(
        "message_context_analyzed",
        platform=platform,
        is_group=is_group,
        urgency=urgency,
        participants_count=len(participants)
    )
    
    return context


async def should_notify(context: MessageContext, user_id: str) -> bool:
    """
    Determine if user should be notified based on message context.
    
    Args:
        context: Message context
        user_id: User identifier
    
    Returns:
        True if user should be notified
    """
    # Always notify urgent messages
    if context.urgency == "urgent":
        return True
    
    # In group messages, only notify if user is mentioned
    if context.is_group:
        # Check if user is mentioned
        return user_id in context.mentioned_users or "@all" in context.mentioned_users
    
    # Personal messages always notify (unless low priority)
    if context.urgency == "low":
        return False
    
    return True

# Made with Bob

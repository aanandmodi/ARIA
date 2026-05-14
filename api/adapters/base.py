"""
Unified inbound message dataclass — the common format for all platform messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InboundMessage:
    """Platform-agnostic inbound message representation."""
    platform: str                        # "gmail" | "whatsapp" | "discord" | "slack" | "sms" | "rss"
    message_id: str                      # platform-native ID
    thread_id: str | None                # platform-native thread/conversation ID
    sender_id: str                       # email / phone / user_id
    sender_name: str                     # display name
    content: str                         # plain text body
    raw: dict                            # original payload for archival
    received_at: datetime                # when the message arrived
    has_attachment: bool = False
    attachment_urls: list[str] = field(default_factory=list)
    audio_url: str | None = None         # for voice notes
    subject: str | None = None           # for emails

    def to_dict(self) -> dict:
        """Serialise to dict for ARQ job passing."""
        return {
            "platform": self.platform,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "raw": self.raw,
            "received_at": self.received_at.isoformat(),
            "has_attachment": self.has_attachment,
            "attachment_urls": self.attachment_urls,
            "audio_url": self.audio_url,
            "subject": self.subject,
        }

    @classmethod
    def from_dict(cls, data: dict) -> InboundMessage:
        """Deserialise from dict (from ARQ job)."""
        received_at = data.get("received_at")
        if isinstance(received_at, str):
            received_at = datetime.fromisoformat(received_at)
        elif not isinstance(received_at, datetime):
            received_at = datetime.utcnow()

        return cls(
            platform=data["platform"],
            message_id=data["message_id"],
            thread_id=data.get("thread_id"),
            sender_id=data["sender_id"],
            sender_name=data.get("sender_name", "Unknown"),
            content=data.get("content", ""),
            raw=data.get("raw", {}),
            received_at=received_at,
            has_attachment=data.get("has_attachment", False),
            attachment_urls=data.get("attachment_urls", []),
            audio_url=data.get("audio_url"),
            subject=data.get("subject"),
        )

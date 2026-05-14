"""
All SQLAlchemy 2 async models for ARIA.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    BigInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared base for every ARIA model."""
    pass


# ─── Messages ────────────────────────────────────────────────────────────────

class Message(Base):
    """Every inbound message from every platform."""
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_platform_created", "platform", "created_at"),
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_external_id", "external_id", unique=True),
        Index("ix_messages_thread_id", "thread_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    sender_id: Mapped[str] = mapped_column(String(256), nullable=False)
    sender_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    needs_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    urgency: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    has_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    attachment_urls: Mapped[list] = mapped_column(JSON, default=list)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    silenced: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_msg_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


# ─── Contacts ────────────────────────────────────────────────────────────────

class Contact(Base):
    """One row per person, updated on each message."""
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_email", "email"),
        Index("ix_contacts_phone", "phone"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    platform_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    topic_tags: Mapped[list] = mapped_column(JSON, default=list)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    avg_response_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        server_default=func.now(),
    )


# ─── Threads ─────────────────────────────────────────────────────────────────

class Thread(Base):
    """Groups messages into conversations."""
    __tablename__ = "threads"
    __table_args__ = (
        Index("ix_threads_platform_ext", "platform", "external_thread_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_thread_id: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_msg_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    message_count: Mapped[int] = mapped_column(Integer, default=0)


# ─── Reminders ────────────────────────────────────────────────────────────────

class Reminder(Base):
    """Scheduled reminders."""
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


# ─── Notes ────────────────────────────────────────────────────────────────────

class Note(Base):
    """Web clips, voice transcripts, manual notes."""
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    notion_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


# ─── Expenses ─────────────────────────────────────────────────────────────────

class Expense(Base):
    """Personal expense tracking."""
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


# ─── Habits ───────────────────────────────────────────────────────────────────

class Habit(Base):
    """Habit tracking with streaks."""
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), default="daily")
    last_done: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


# ─── Watchlist ────────────────────────────────────────────────────────────────

class Watchlist(Base):
    """Stocks, crypto, product prices, keyword alerts."""
    __tablename__ = "watchlist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    target: Mapped[str] = mapped_column(String(256), nullable=False)
    threshold: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    last_value: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    last_alert: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ─── Telegram Session ────────────────────────────────────────────────────────

class TelegramSession(Base):
    """Tracks which message the Telegram user is replying to."""
    __tablename__ = "telegram_sessions"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_platform: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="idle")
    draft_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        server_default=func.now(),
    )

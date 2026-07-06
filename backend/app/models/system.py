"""Uploaded files, notifications, and chat history
(Docs/04_Database_Design.md §11–§13)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ChatRole, FileCategory, ParsingStatus

if TYPE_CHECKING:
    from app.models.user import User


class UploadedFile(Base, UUIDPrimaryKeyMixin):
    """Metadata for a file in Supabase Storage. V1 stores only the timetable, one
    per user — a new upload replaces the previous one (§11)."""

    __tablename__ = "uploaded_files"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_category: Mapped[FileCategory] = mapped_column(
        SQLEnum(FileCategory, native_enum=False, length=20),
        default=FileCategory.TIMETABLE,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    parsing_status: Mapped[ParsingStatus] = mapped_column(
        SQLEnum(ParsingStatus, native_enum=False, length=20),
        default=ParsingStatus.PENDING,
        nullable=False,
    )
    parsing_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="uploaded_files")


class Notification(Base, UUIDPrimaryKeyMixin):
    """Scheduled browser notification (§12)."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="notifications")


class ChatMessage(Base, UUIDPrimaryKeyMixin):
    """One message in a conversation with Coco (§13)."""

    __tablename__ = "chat_messages"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    role: Mapped[ChatRole] = mapped_column(
        SQLEnum(ChatRole, native_enum=False, length=10), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chat_messages")

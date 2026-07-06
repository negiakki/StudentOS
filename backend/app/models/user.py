"""User profile and settings (Docs/04_Database_Design.md §4, §14)."""

from __future__ import annotations

import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.academic import Subject
    from app.models.planning import Assignment, Todo
    from app.models.system import ChatMessage, Notification, UploadedFile


class User(Base, TimestampMixin):
    """StudentOS profile. `id` is the Supabase Auth user id — never generated
    here, always taken from the verified JWT `sub`. No passwords are ever stored."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text)
    college: Mapped[str | None] = mapped_column(Text)
    degree: Mapped[str | None] = mapped_column(Text)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships (cascade delete powers the account-deletion flow, §16).
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    todos: Mapped[list["Todo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped["Settings"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Settings(Base, TimestampMixin):
    """User preferences (§14)."""

    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    reminder_time: Mapped[time | None] = mapped_column(Time)
    attendance_threshold: Mapped[int] = mapped_column(
        Integer, default=75, nullable=False
    )
    preferred_ai_provider: Mapped[str | None] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="settings")

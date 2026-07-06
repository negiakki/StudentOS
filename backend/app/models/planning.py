"""Assignments and todos (Docs/04_Database_Design.md §9, §10)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AssignmentStatus, Priority

if TYPE_CHECKING:
    from app.models.academic import Subject
    from app.models.user import User


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Coursework item. Subject is optional (§9)."""

    __tablename__ = "assignments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority, native_enum=False, length=10),
        default=Priority.MEDIUM,
        nullable=False,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SQLEnum(AssignmentStatus, native_enum=False, length=20),
        default=AssignmentStatus.PENDING,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="assignments")
    subject: Mapped["Subject | None"] = relationship()


class Todo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simple checklist task (§10)."""

    __tablename__ = "todos"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority, native_enum=False, length=10),
        default=Priority.MEDIUM,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="todos")

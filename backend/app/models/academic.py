"""Subjects, timetable slots, and attendance (Docs/04_Database_Design.md §5–§8)."""

from __future__ import annotations

import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AttendanceStatus

if TYPE_CHECKING:
    from app.models.user import User


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A course belonging to one user (e.g. DBMS)."""

    __tablename__ = "subjects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    faculty: Mapped[str | None] = mapped_column(Text)
    classroom: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="subjects")
    timetable_slots: Mapped[list["TimetableSlot"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    attendance_summary: Mapped["AttendanceSummary"] = relationship(
        back_populates="subject", cascade="all, delete-orphan", uselist=False
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class TimetableSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One scheduled lecture. `day_of_week` is 1 (Mon) .. 7 (Sun)."""

    __tablename__ = "timetable_slots"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(Text)

    subject: Mapped["Subject"] = relationship(back_populates="timetable_slots")


class AttendanceSummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Latest attendance totals per subject, for fast dashboard reads. Percentage
    and safe-skips are NEVER stored — they are always calculated (§7)."""

    __tablename__ = "attendance_summary"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    attended_classes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="attendance_summary")


class AttendanceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One subject on one date. Changing a record recomputes the summary (§8)."""

    __tablename__ = "attendance_records"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attendance_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus, native_enum=False, length=20), nullable=False
    )

    subject: Mapped["Subject"] = relationship(back_populates="attendance_records")

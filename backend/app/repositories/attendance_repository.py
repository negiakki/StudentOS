"""Attendance data access (Phase 5 summary + Phase 6 daily records).

Repositories only read/write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). Subjects are reused from the timetable
repository; this adds the per-subject attendance summary row and the day-by-day
attendance records.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select

from app.models.academic import AttendanceRecord, AttendanceSummary, Subject
from app.repositories.base import BaseRepository


class AttendanceSummaryRepository(BaseRepository[AttendanceSummary]):
    model = AttendanceSummary

    def get_by_subject(self, subject_id: uuid.UUID) -> AttendanceSummary | None:
        return self.db.scalar(
            select(AttendanceSummary).where(
                AttendanceSummary.subject_id == subject_id
            )
        )

    def list_for_user(self, user_id: uuid.UUID) -> list[AttendanceSummary]:
        """Every summary belonging to the user, joined through their subjects.

        `AttendanceSummary` has no `user_id`; ownership flows through the parent
        subject (Docs/04_Database_Design.md §7)."""
        return list(
            self.db.scalars(
                select(AttendanceSummary)
                .join(Subject, AttendanceSummary.subject_id == Subject.id)
                .where(Subject.user_id == user_id)
            )
        )


class AttendanceRecordRepository(BaseRepository[AttendanceRecord]):
    """Day-by-day attendance marks. One record per (subject, date); ownership
    flows through the parent subject, so callers must resolve the subject for the
    user first (Docs/04_Database_Design.md §8, §18)."""

    model = AttendanceRecord

    def get_by_subject_and_date(
        self, subject_id: uuid.UUID, on_date: date
    ) -> AttendanceRecord | None:
        return self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.subject_id == subject_id,
                AttendanceRecord.attendance_date == on_date,
            )
        )

    def list_range(
        self, subject_id: uuid.UUID, start: date, end: date
    ) -> list[AttendanceRecord]:
        """Records within [start, end], ascending — for a calendar month."""
        return list(
            self.db.scalars(
                select(AttendanceRecord)
                .where(
                    AttendanceRecord.subject_id == subject_id,
                    AttendanceRecord.attendance_date >= start,
                    AttendanceRecord.attendance_date <= end,
                )
                .order_by(AttendanceRecord.attendance_date)
            )
        )

    def list_recent(
        self, subject_id: uuid.UUID, limit: int
    ) -> list[AttendanceRecord]:
        """Most recent records first — for the attendance-history list."""
        return list(
            self.db.scalars(
                select(AttendanceRecord)
                .where(AttendanceRecord.subject_id == subject_id)
                .order_by(AttendanceRecord.attendance_date.desc())
                .limit(limit)
            )
        )

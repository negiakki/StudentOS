"""Attendance data access (Phase 5).

Repositories only read/write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). Subjects are reused from the timetable
repository; this adds the per-subject attendance summary row.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.academic import AttendanceSummary, Subject
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

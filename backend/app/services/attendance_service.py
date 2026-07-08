"""Attendance business logic (Phase 5 — manual attendance).

Python performs every calculation; the database stores only raw counts
(Docs/03_System_Architecture.md §5, §16; Docs/04_Database_Design.md §1). V1 is
manual: subjects and their attended/total counts come from the user. Daily
marking, the calendar, and edit-previous-days are Phase 6.
"""

from __future__ import annotations

import math
import uuid

from sqlalchemy.orm import Session

from app.models.academic import AttendanceSummary, Subject
from app.repositories.attendance_repository import AttendanceSummaryRepository
from app.repositories.timetable_repository import SubjectRepository
from app.schemas.attendance import (
    AttendanceOverview,
    SubjectAttendance,
    SubjectCreate,
    SubjectUpdate,
)

# V1 uses a fixed threshold matching the schema default (Docs/04 §14). Per-user
# thresholds via Settings are a later enhancement.
DEFAULT_ATTENDANCE_THRESHOLD = 75


def attendance_percentage(attended: int, total: int) -> float:
    """Attended / total as a percentage, rounded to one decimal. 0 if no classes."""
    if total <= 0:
        return 0.0
    return round(attended / total * 100, 1)


def safe_skips(attended: int, total: int, threshold: int) -> int:
    """How many upcoming classes can be missed while staying at/above threshold.

    Skipping k future classes leaves `attended` unchanged and raises `total` by k;
    we need attended / (total + k) >= threshold/100, i.e. k <= attended*100/threshold - total.
    Returns 0 when already below threshold or when the threshold is non-positive.
    """
    if threshold <= 0 or total <= 0:
        return 0
    limit = attended * 100 / threshold - total
    return max(0, math.floor(limit))


class AttendanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.subjects = SubjectRepository(db)
        self.summaries = AttendanceSummaryRepository(db)
        self.threshold = DEFAULT_ATTENDANCE_THRESHOLD

    def add_subject(
        self, *, user_id: uuid.UUID, payload: SubjectCreate
    ) -> SubjectAttendance:
        """Create a subject and its attendance summary from user-entered counts."""
        subject = Subject(user_id=user_id, name=payload.name.strip())
        self.subjects.add(subject)
        summary = AttendanceSummary(
            subject_id=subject.id,
            attended_classes=payload.attended_classes,
            total_classes=payload.total_classes,
        )
        self.summaries.add(summary)
        return self._to_subject_attendance(subject, summary)

    def list_subjects(self, *, user_id: uuid.UUID) -> list[SubjectAttendance]:
        return [item for item, _ in self._subjects_with_summaries(user_id)]

    def update_subject(
        self, *, user_id: uuid.UUID, subject_id: uuid.UUID, payload: SubjectUpdate
    ) -> SubjectAttendance | None:
        """Edit a subject's name and/or counts. Returns None if not owned/found."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return None
        summary = self.summaries.get_by_subject(subject_id)
        if summary is None:
            summary = AttendanceSummary(
                subject_id=subject_id, attended_classes=0, total_classes=0
            )
            self.summaries.add(summary)

        if payload.name is not None:
            subject.name = payload.name.strip()
        if payload.total_classes is not None:
            summary.total_classes = payload.total_classes
        if payload.attended_classes is not None:
            summary.attended_classes = payload.attended_classes
        # Keep the invariant attended <= total after a partial edit.
        if summary.attended_classes > summary.total_classes:
            summary.attended_classes = summary.total_classes

        self.db.flush()
        return self._to_subject_attendance(subject, summary)

    def delete_subject(self, *, user_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        """Delete a subject (summary cascades). Returns False if not owned/found."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return False
        self.subjects.delete(subject)
        return True

    def overview(self, *, user_id: uuid.UUID) -> AttendanceOverview:
        """Aggregate summary across all subjects for the dashboard."""
        items = [item for item, _ in self._subjects_with_summaries(user_id)]
        attended_total = sum(i.attended_classes for i in items)
        total_total = sum(i.total_classes for i in items)
        return AttendanceOverview(
            threshold=self.threshold,
            subject_count=len(items),
            attended_total=attended_total,
            total_total=total_total,
            overall_percentage=attendance_percentage(attended_total, total_total),
            below_threshold_count=sum(1 for i in items if not i.meets_threshold),
            subjects=items,
        )

    # --- internals ---

    def _subjects_with_summaries(
        self, user_id: uuid.UUID
    ) -> list[tuple[SubjectAttendance, Subject]]:
        """Subjects (with computed attendance), name-sorted, each paired with its ORM row."""
        result: list[tuple[SubjectAttendance, Subject]] = []
        for subject in sorted(
            self.subjects.list_for_user(user_id), key=lambda s: s.name.lower()
        ):
            summary = self.summaries.get_by_subject(subject.id)
            result.append((self._to_subject_attendance(subject, summary), subject))
        return result

    def _to_subject_attendance(
        self, subject: Subject, summary: AttendanceSummary | None
    ) -> SubjectAttendance:
        attended = summary.attended_classes if summary else 0
        total = summary.total_classes if summary else 0
        pct = attendance_percentage(attended, total)
        return SubjectAttendance(
            id=subject.id,
            name=subject.name,
            attended_classes=attended,
            total_classes=total,
            percentage=pct,
            safe_skips=safe_skips(attended, total, self.threshold),
            # No classes yet → treat as meeting the threshold (nothing to warn about).
            meets_threshold=(total == 0) or (pct >= self.threshold),
        )

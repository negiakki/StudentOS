"""Attendance business logic (Phase 5 setup + Phase 6 daily marking).

Python performs every calculation; the database stores only raw counts
(Docs/03_System_Architecture.md §5, §16; Docs/04_Database_Design.md §1). Setup
is manual: subjects and their attended/total baseline come from the user. Phase 6
adds day-by-day marking — each record adjusts the stored summary as a delta, so
percentage / safe-skips stay derived, and the calendar and history read the same
records (Docs/04 §8).
"""

from __future__ import annotations

import math
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.academic import AttendanceRecord, AttendanceSummary, Subject
from app.models.enums import AttendanceStatus
from app.repositories.attendance_repository import (
    AttendanceRecordRepository,
    AttendanceSummaryRepository,
)
from app.repositories.timetable_repository import SubjectRepository
from app.schemas.attendance import (
    AttendanceOverview,
    AttendanceRecordOut,
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
        self.records = AttendanceRecordRepository(db)
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

    # --- Phase 6: daily marking, calendar, history ---

    def get_subject(
        self, *, user_id: uuid.UUID, subject_id: uuid.UUID
    ) -> SubjectAttendance | None:
        """A single subject's computed attendance. None if not owned/found."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return None
        summary = self.summaries.get_by_subject(subject_id)
        return self._to_subject_attendance(subject, summary)

    def mark(
        self,
        *,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
        on_date: date,
        status: AttendanceStatus,
    ) -> tuple[SubjectAttendance, AttendanceRecordOut] | None:
        """Set the subject's status for one day (create or edit the record) and
        adjust the summary by the delta. Returns None if not owned/found."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return None
        summary = self._get_or_create_summary(subject_id)
        existing = self.records.get_by_subject_and_date(subject_id, on_date)

        if existing is None:
            # A newly recorded class: one more class, present raises attended too.
            record = AttendanceRecord(
                subject_id=subject_id, attendance_date=on_date, status=status
            )
            self.records.add(record)
            summary.total_classes += 1
            if status == AttendanceStatus.PRESENT:
                summary.attended_classes += 1
        else:
            # Editing an existing day: total is unchanged; attended shifts by ±1.
            record = existing
            if existing.status != status:
                if status == AttendanceStatus.PRESENT:
                    summary.attended_classes += 1
                else:
                    summary.attended_classes -= 1
                existing.status = status

        self._clamp(summary)
        self.db.flush()
        return (
            self._to_subject_attendance(subject, summary),
            self._to_record_out(record),
        )

    def unmark(
        self, *, user_id: uuid.UUID, subject_id: uuid.UUID, on_date: date
    ) -> SubjectAttendance | None:
        """Clear a day's record, reversing its effect on the summary. Idempotent.
        Returns None if the subject is not owned/found."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return None
        summary = self._get_or_create_summary(subject_id)
        existing = self.records.get_by_subject_and_date(subject_id, on_date)
        if existing is not None:
            summary.total_classes -= 1
            if existing.status == AttendanceStatus.PRESENT:
                summary.attended_classes -= 1
            self.records.delete(existing)
            self._clamp(summary)
            self.db.flush()
        return self._to_subject_attendance(subject, summary)

    def list_records(
        self,
        *,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
        start: date | None = None,
        end: date | None = None,
        limit: int | None = None,
    ) -> list[AttendanceRecordOut] | None:
        """Records for the calendar (``start``/``end`` range) or the history list
        (most recent ``limit``, default 30). None if the subject isn't owned."""
        subject = self.subjects.get_for_user(subject_id, user_id)
        if subject is None:
            return None
        if start is not None and end is not None:
            rows = self.records.list_range(subject_id, start, end)
        else:
            rows = self.records.list_recent(subject_id, limit or 30)
        return [self._to_record_out(r) for r in rows]

    # --- internals ---

    def _get_or_create_summary(self, subject_id: uuid.UUID) -> AttendanceSummary:
        summary = self.summaries.get_by_subject(subject_id)
        if summary is None:
            summary = AttendanceSummary(
                subject_id=subject_id, attended_classes=0, total_classes=0
            )
            self.summaries.add(summary)
        return summary

    @staticmethod
    def _clamp(summary: AttendanceSummary) -> None:
        """Defensive: keep counts non-negative and attended within total."""
        summary.total_classes = max(0, summary.total_classes)
        summary.attended_classes = max(
            0, min(summary.attended_classes, summary.total_classes)
        )

    @staticmethod
    def _to_record_out(record: AttendanceRecord) -> AttendanceRecordOut:
        return AttendanceRecordOut(
            id=record.id,
            attendance_date=record.attendance_date,
            status=record.status,
        )

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

"""Attendance API schemas (Phase 5 setup + Phase 6 daily marking).

V1 attendance starts fully manual: the user creates their semester subjects and
enters classes attended / total (a baseline). Phase 6 adds day-by-day marking
(present/absent) via attendance records; each mark adjusts the stored summary,
so percentage, safe-skips, and the threshold warning stay always CALCULATED by
the backend, never stored (Docs/04_Database_Design.md §1, §7, §8).
"""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AttendanceStatus


class SubjectCreate(BaseModel):
    """A subject the user adds during attendance setup."""

    name: str = Field(min_length=1, max_length=120)
    attended_classes: int = Field(ge=0)
    total_classes: int = Field(ge=0)

    @model_validator(mode="after")
    def _attended_within_total(self) -> "SubjectCreate":
        if self.attended_classes > self.total_classes:
            raise ValueError("attended_classes cannot exceed total_classes")
        return self


class SubjectUpdate(BaseModel):
    """Partial edit of a subject's name or attendance counts."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    attended_classes: int | None = Field(default=None, ge=0)
    total_classes: int | None = Field(default=None, ge=0)


class SubjectAttendance(BaseModel):
    """A subject with its stored counts and the backend-computed figures."""

    id: uuid.UUID
    name: str
    attended_classes: int
    total_classes: int
    percentage: float
    safe_skips: int
    meets_threshold: bool


class AttendanceOverview(BaseModel):
    """Dashboard summary across all of the user's subjects."""

    threshold: int
    subject_count: int
    attended_total: int
    total_total: int
    overall_percentage: float
    below_threshold_count: int
    subjects: list[SubjectAttendance] = Field(default_factory=list)


# --- Phase 6: daily marking ---------------------------------------------------


class RecordUpsert(BaseModel):
    """Set a subject's status for a single day (present or absent)."""

    status: AttendanceStatus


class AttendanceRecordOut(BaseModel):
    """One subject's marked status on one date. Powers both the calendar and the
    attendance-history list, which read the same records (Docs/04 §8)."""

    id: uuid.UUID
    attendance_date: date
    status: AttendanceStatus


class RecordMutationResult(BaseModel):
    """Result of marking / clearing a day: the recomputed subject figures plus the
    affected record (``None`` when the day was cleared)."""

    subject: SubjectAttendance
    record: AttendanceRecordOut | None = None

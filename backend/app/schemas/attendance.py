"""Attendance API schemas (Phase 5 — manual attendance).

V1 attendance is fully manual: the user creates their semester subjects and
enters classes attended / total. Percentage, safe-skips, and the threshold
warning are always CALCULATED by the backend, never stored
(Docs/04_Database_Design.md §1, §7). Daily marking / calendar is Phase 6.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator


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

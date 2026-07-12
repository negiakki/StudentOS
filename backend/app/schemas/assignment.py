"""Assignment API schemas (Phase 7).

An assignment is coursework the user tracks by due date; `subject_id` is
optional (Docs/04_Database_Design.md §9). The dashboard groups assignments into
Today / Upcoming / Overdue — the grouping is CALCULATED by the service from
`due_date` and `status`, never stored (Docs/03_System_Architecture.md §5, §16).
"""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssignmentStatus, Priority


class AssignmentCreate(BaseModel):
    """A new assignment. `status` always starts PENDING."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    subject_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM


class AssignmentUpdate(BaseModel):
    """Partial edit of an assignment, including marking it complete/pending."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    subject_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: Priority | None = None
    status: AssignmentStatus | None = None


class AssignmentOut(BaseModel):
    """An assignment as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID | None
    title: str
    description: str | None
    due_date: date | None
    priority: Priority
    status: AssignmentStatus


class AssignmentDashboard(BaseModel):
    """Assignments grouped by due date, for the dashboard.

    Only PENDING assignments are grouped: completed work has nothing left to
    track by due date. `today` is due exactly today, `overdue` is due before
    today, `upcoming` is due after today (or has no due date).
    """

    today: list[AssignmentOut] = Field(default_factory=list)
    upcoming: list[AssignmentOut] = Field(default_factory=list)
    overdue: list[AssignmentOut] = Field(default_factory=list)

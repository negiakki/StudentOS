"""Assignment business logic (Phase 7).

Python performs every calculation; the database stores only raw fields
(Docs/03_System_Architecture.md §5, §16). The dashboard's Today / Upcoming /
Overdue grouping is computed here from `due_date` and `status`, never stored.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.enums import AssignmentStatus
from app.models.planning import Assignment
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.timetable_repository import SubjectRepository
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentDashboard,
    AssignmentOut,
    AssignmentUpdate,
)


class InvalidSubjectError(Exception):
    """Raised when `subject_id` doesn't reference a subject owned by the user."""


class AssignmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assignments = AssignmentRepository(db)
        self.subjects = SubjectRepository(db)

    def create(
        self, *, user_id: uuid.UUID, payload: AssignmentCreate
    ) -> AssignmentOut:
        """Add an assignment. Always starts PENDING.

        Raises `InvalidSubjectError` if `subject_id` is set but isn't owned by
        the user (or doesn't exist).
        """
        self._ensure_subject_owned(user_id=user_id, subject_id=payload.subject_id)
        assignment = Assignment(
            user_id=user_id,
            subject_id=payload.subject_id,
            title=payload.title.strip(),
            description=payload.description,
            due_date=payload.due_date,
            priority=payload.priority,
            status=AssignmentStatus.PENDING,
        )
        self.assignments.add(assignment)
        return self._to_out(assignment)

    def list(self, *, user_id: uuid.UUID) -> list[AssignmentOut]:
        """All of the user's assignments, soonest due date first (undated last)."""
        items = self.assignments.list_for_user(user_id)
        items.sort(key=self._sort_key)
        return [self._to_out(a) for a in items]

    def get(
        self, *, user_id: uuid.UUID, assignment_id: uuid.UUID
    ) -> AssignmentOut | None:
        """A single assignment. None if not owned/found."""
        assignment = self.assignments.get_for_user(assignment_id, user_id)
        if assignment is None:
            return None
        return self._to_out(assignment)

    def update(
        self,
        *,
        user_id: uuid.UUID,
        assignment_id: uuid.UUID,
        payload: AssignmentUpdate,
    ) -> AssignmentOut | None:
        """Edit an assignment, including marking it complete/pending. None if not
        owned/found.

        Raises `InvalidSubjectError` if `subject_id` is set but isn't owned by
        the user (or doesn't exist).
        """
        assignment = self.assignments.get_for_user(assignment_id, user_id)
        if assignment is None:
            return None
        fields = payload.model_fields_set
        if "subject_id" in fields:
            self._ensure_subject_owned(user_id=user_id, subject_id=payload.subject_id)

        if payload.title is not None:
            assignment.title = payload.title.strip()
        # description/subject_id/due_date are nullable and clearable, so apply
        # them whenever the client sent the field at all (even as null) —
        # `is not None` would make it impossible to ever clear them back out.
        if "description" in fields:
            assignment.description = payload.description
        if "subject_id" in fields:
            assignment.subject_id = payload.subject_id
        if "due_date" in fields:
            assignment.due_date = payload.due_date
        if payload.priority is not None:
            assignment.priority = payload.priority
        if payload.status is not None:
            assignment.status = payload.status

        self.db.flush()
        return self._to_out(assignment)

    def delete(self, *, user_id: uuid.UUID, assignment_id: uuid.UUID) -> bool:
        """Delete an assignment. Returns False if not owned/found."""
        assignment = self.assignments.get_for_user(assignment_id, user_id)
        if assignment is None:
            return False
        self.assignments.delete(assignment)
        return True

    def dashboard(self, *, user_id: uuid.UUID) -> AssignmentDashboard:
        """Group the user's PENDING assignments into Today / Upcoming / Overdue.

        Completed assignments have nothing left to track by due date, so they're
        excluded. Undated assignments are treated as Upcoming (nothing to be
        overdue against).
        """
        today = date.today()
        pending = [
            a
            for a in self.assignments.list_for_user(user_id)
            if a.status == AssignmentStatus.PENDING
        ]

        due_today = [a for a in pending if a.due_date == today]
        overdue = [a for a in pending if a.due_date is not None and a.due_date < today]
        upcoming = [
            a for a in pending if a.due_date is None or a.due_date > today
        ]

        due_today.sort(key=self._sort_key)
        overdue.sort(key=self._sort_key)
        upcoming.sort(key=self._sort_key)

        return AssignmentDashboard(
            today=[self._to_out(a) for a in due_today],
            upcoming=[self._to_out(a) for a in upcoming],
            overdue=[self._to_out(a) for a in overdue],
        )

    # --- internals ---

    def _ensure_subject_owned(
        self, *, user_id: uuid.UUID, subject_id: uuid.UUID | None
    ) -> None:
        """No-op if `subject_id` is None; otherwise raise `InvalidSubjectError`
        unless it's owned by the user."""
        if subject_id is None:
            return
        if self.subjects.get_for_user(subject_id, user_id) is None:
            raise InvalidSubjectError(f"Subject {subject_id} not found.")

    @staticmethod
    def _sort_key(assignment: Assignment) -> tuple[bool, date, str]:
        """Soonest due date first; undated assignments sort last."""
        return (
            assignment.due_date is None,
            assignment.due_date or date.max,
            assignment.title.lower(),
        )

    @staticmethod
    def _to_out(assignment: Assignment) -> AssignmentOut:
        return AssignmentOut.model_validate(assignment)

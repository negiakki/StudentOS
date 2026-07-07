"""Timetable-related repositories: uploaded files, subjects, and slots.

Repositories only read and write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). Every query is scoped to the authenticated
user (Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.academic import Subject, TimetableSlot
from app.models.system import UploadedFile
from app.repositories.base import UserScopedRepository


class UploadedFileRepository(UserScopedRepository[UploadedFile]):
    model = UploadedFile

    def get_timetable_for_user(self, user_id: uuid.UUID) -> UploadedFile | None:
        """The user's single timetable upload, if any. V1 keeps one per user
        (Docs/04_Database_Design.md §11)."""
        return self.db.scalar(
            select(UploadedFile).where(UploadedFile.user_id == user_id)
        )


class SubjectRepository(UserScopedRepository[Subject]):
    model = Subject


class TimetableSlotRepository(UserScopedRepository[TimetableSlot]):
    model = TimetableSlot

    def list_for_user(self, user_id: uuid.UUID) -> list[TimetableSlot]:
        """All slots belonging to the user, joined through their subjects.

        `TimetableSlot` has no `user_id` of its own; ownership flows through the
        parent subject, so this overrides the base scoped query.
        """
        return list(
            self.db.scalars(
                select(TimetableSlot)
                .join(Subject, TimetableSlot.subject_id == Subject.id)
                .where(Subject.user_id == user_id)
            )
        )

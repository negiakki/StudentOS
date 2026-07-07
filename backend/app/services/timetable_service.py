"""Timetable business logic (Docs/03_System_Architecture.md §7, §11).

Owns the two-step upload flow:

  1. upload_and_parse — store the file in Supabase Storage, run the AI parser,
     record upload metadata, and return a *preview* (nothing academic is saved
     yet; the user reviews and edits it first).
  2. save_timetable — persist the user-confirmed subjects + slots, replacing any
     existing timetable (V1: one timetable per user, Docs/04_Database_Design.md §11).

Services own logic and delegate persistence to repositories. All state changes
happen on the session and are committed by the request-scoped `get_db` dependency.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ai.timetable_parser import ParseResult, TimetableParser
from app.models.academic import Subject, TimetableSlot
from app.models.enums import FileCategory, ParsingStatus
from app.models.system import UploadedFile
from app.repositories.timetable_repository import (
    SubjectRepository,
    TimetableSlotRepository,
    UploadedFileRepository,
)
from app.schemas.timetable import (
    SlotPreview,
    SubjectInput,
    SubjectPreview,
    TimetableOut,
    TimetablePreview,
)
from app.services.storage_service import StorageService

# Uploaded timetables are stored under a fixed name per user (one per user), so a
# re-upload overwrites the previous object. Extension tracks the upload's type.
_EXTENSION_BY_MIME = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
}


class TimetableService:
    def __init__(
        self,
        db: Session,
        *,
        storage: StorageService | None = None,
        parser: TimetableParser | None = None,
    ) -> None:
        self.db = db
        self.files = UploadedFileRepository(db)
        self.subjects = SubjectRepository(db)
        self.slots = TimetableSlotRepository(db)
        # Injectable for testing; constructed lazily by default.
        self._storage = storage
        self._parser = parser

    @property
    def storage(self) -> StorageService:
        if self._storage is None:
            self._storage = StorageService()
        return self._storage

    @property
    def parser(self) -> TimetableParser:
        if self._parser is None:
            self._parser = TimetableParser()
        return self._parser

    # --- Step 1: upload + parse -> preview ---

    def upload_and_parse(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> TimetablePreview:
        """Store the upload, parse it, and return a preview for user confirmation.

        The uploaded file replaces any previous timetable object in storage and
        its metadata row. Academic data (subjects/slots) is NOT touched here —
        only after the user confirms via `save_timetable`.
        """
        extension = _EXTENSION_BY_MIME.get(content_type, "bin")
        stored_name = f"timetable.{extension}"

        # Replace the previous storage object (if any) at the stable user path.
        storage_path = self.storage.upload(
            user_id=user_id,
            filename=stored_name,
            content=content,
            content_type=content_type,
        )

        result = self.parser.parse(content=content, mime_type=content_type)

        upload = self._record_upload(
            user_id=user_id,
            filename=filename,
            storage_path=storage_path,
            mime_type=content_type,
            result=result,
        )

        return TimetablePreview(
            file_id=upload.id,
            parsing_status=upload.parsing_status.value,
            parsing_confidence=upload.parsing_confidence,
            parse_error=result.error,
            subjects=[
                SubjectPreview(
                    name=subject.name,
                    faculty=subject.faculty,
                    classroom=subject.classroom,
                    slots=[
                        SlotPreview(
                            day_of_week=slot.day_of_week,
                            start_time=slot.start_time,
                            end_time=slot.end_time,
                            room=slot.room,
                        )
                        for slot in subject.slots
                    ],
                )
                for subject in result.subjects
            ],
        )

    def _record_upload(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        storage_path: str,
        mime_type: str,
        result: ParseResult,
    ) -> UploadedFile:
        """Upsert the user's single uploaded-file metadata row (§11)."""
        status = ParsingStatus.SUCCESS if result.succeeded else ParsingStatus.FAILED
        confidence = result.confidence if result.succeeded else None

        upload = self.files.get_timetable_for_user(user_id)
        if upload is None:
            upload = UploadedFile(
                user_id=user_id,
                file_category=FileCategory.TIMETABLE,
                filename=filename,
                storage_path=storage_path,
                mime_type=mime_type,
                parsing_status=status,
                parsing_confidence=confidence,
            )
            self.files.add(upload)
        else:
            upload.filename = filename
            upload.storage_path = storage_path
            upload.mime_type = mime_type
            upload.parsing_status = status
            upload.parsing_confidence = confidence
            self.db.flush()
        return upload

    # --- Step 2: confirm -> save ---

    def save_timetable(
        self, *, user_id: uuid.UUID, subjects: list[SubjectInput]
    ) -> TimetableOut:
        """Persist the user-confirmed timetable, replacing any existing one.

        V1 keeps a single timetable per user, so we clear the user's current
        subjects (cascading to their slots) and recreate from the confirmed data.
        """
        for existing in self.subjects.list_for_user(user_id):
            # Cascade removes the subject's slots, summary, and records.
            self.subjects.delete(existing)

        saved: list[Subject] = []
        for subject_input in subjects:
            subject = Subject(
                user_id=user_id,
                name=subject_input.name,
                faculty=subject_input.faculty,
                classroom=subject_input.classroom,
            )
            self.subjects.add(subject)
            for slot_input in subject_input.slots:
                self.slots.add(
                    TimetableSlot(
                        subject_id=subject.id,
                        day_of_week=slot_input.day_of_week,
                        start_time=slot_input.start_time,
                        end_time=slot_input.end_time,
                        room=slot_input.room,
                    )
                )
            saved.append(subject)

        self.db.flush()
        return self._to_out(saved)

    # --- Read ---

    def get_timetable(self, *, user_id: uuid.UUID) -> TimetableOut:
        """The user's saved subjects with their slots (empty if none)."""
        subjects = self.subjects.list_for_user(user_id)
        return self._to_out(subjects)

    @staticmethod
    def _to_out(subjects: list[Subject]) -> TimetableOut:
        from app.schemas.timetable import SlotOut, SubjectOut

        return TimetableOut(
            subjects=[
                SubjectOut(
                    id=subject.id,
                    name=subject.name,
                    faculty=subject.faculty,
                    classroom=subject.classroom,
                    slots=sorted(
                        (SlotOut.model_validate(slot) for slot in subject.timetable_slots),
                        key=lambda s: (s.day_of_week, s.start_time),
                    ),
                )
                for subject in subjects
            ]
        )

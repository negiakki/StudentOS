"""Timetable business logic (Docs/03_System_Architecture.md §7, §11).

V1 (storage-only) — the active flow:
  upload_file  — store the file in Supabase Storage and save its reference. No AI.
  get_file     — return the current file reference + a signed view URL.
  delete_file  — remove the stored object and its metadata row.

Preserved for V2 (automatic parsing, gated by `ENABLE_TIMETABLE_PARSING`):
  upload_and_parse — store + parse via the vision router → editable preview.
  save_timetable / get_timetable — persist / read confirmed subjects + slots.

Services own logic and delegate persistence to repositories. State changes happen
on the session and are committed by the request-scoped `get_db` dependency.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ai.timetable_parser import ParseResult, TimetableParser
from app.core.config import get_settings
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
    TimetableFile,
    TimetableFileState,
    TimetableOut,
    TimetablePreview,
)
from app.services.storage_service import StorageService

# One timetable per user: the stored object uses a fixed name per file type, so a
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

    # =====================================================================
    # V1 — storage-only upload (no AI)
    # =====================================================================

    def upload_file(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> TimetableFile:
        """Store the uploaded timetable and save its reference. No AI is called.

        Replaces any previous timetable for the user (one per user, §11): the
        stored object is overwritten in place and the metadata row is upserted.
        Returns the file reference with a signed URL for immediate display.
        """
        upload = self._store_and_record(
            user_id=user_id,
            filename=filename,
            content=content,
            content_type=content_type,
        )
        return self._to_file(upload)

    def get_file(self, *, user_id: uuid.UUID) -> TimetableFileState:
        """Return the user's uploaded timetable file reference, if any."""
        upload = self.files.get_timetable_for_user(user_id)
        if upload is None:
            return TimetableFileState(has_file=False, file=None)
        return TimetableFileState(has_file=True, file=self._to_file(upload))

    def delete_file(self, *, user_id: uuid.UUID) -> bool:
        """Delete the user's timetable file (storage object + metadata row).

        Returns True if a file existed and was removed, False if there was none.
        Subjects/slots (populated only in V2) are left untouched.
        """
        upload = self.files.get_timetable_for_user(user_id)
        if upload is None:
            return False

        self.storage.delete(upload.storage_path)
        self.files.delete(upload)
        return True

    def _store_and_record(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
        result: ParseResult | None = None,
    ) -> UploadedFile:
        """Upload to storage and upsert the user's single uploaded-file row (§11).

        `result` is None for the storage-only path (parsing_status = PENDING).
        When a parse ran (V2), it sets SUCCESS/FAILED + confidence.
        """
        extension = _EXTENSION_BY_MIME.get(content_type, "bin")
        stored_name = f"timetable.{extension}"
        new_path = self.storage.build_object_path(user_id, stored_name)

        existing = self.files.get_timetable_for_user(user_id)
        # If the file type changed, the old object lives at a different path —
        # remove it so we don't leave an orphan behind.
        if existing is not None and existing.storage_path != new_path:
            self.storage.delete(existing.storage_path)

        storage_path = self.storage.upload(
            user_id=user_id,
            filename=stored_name,
            content=content,
            content_type=content_type,
        )

        if result is None:
            status = ParsingStatus.PENDING
            confidence: Decimal | None = None
        else:
            status = ParsingStatus.SUCCESS if result.succeeded else ParsingStatus.FAILED
            confidence = result.confidence if result.succeeded else None

        if existing is None:
            upload = UploadedFile(
                user_id=user_id,
                file_category=FileCategory.TIMETABLE,
                filename=filename,
                storage_path=storage_path,
                mime_type=content_type,
                parsing_status=status,
                parsing_confidence=confidence,
            )
            self.files.add(upload)
        else:
            existing.filename = filename
            existing.storage_path = storage_path
            existing.mime_type = content_type
            existing.parsing_status = status
            existing.parsing_confidence = confidence
            self.db.flush()
            upload = existing
        return upload

    def _to_file(self, upload: UploadedFile) -> TimetableFile:
        return TimetableFile(
            id=upload.id,
            filename=upload.filename,
            mime_type=upload.mime_type,
            storage_path=upload.storage_path,
            uploaded_at=upload.uploaded_at,
            view_url=self.storage.create_signed_url(upload.storage_path),
        )

    # =====================================================================
    # V2 — automatic parsing (preserved; gated by ENABLE_TIMETABLE_PARSING)
    # =====================================================================

    def upload_and_parse(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> TimetablePreview:
        """Store the upload, parse it via the vision router, and return a preview.

        Preserved for V2. Guarded so it is never reachable while automatic
        parsing is disabled. Academic data is not saved here — only after the
        user confirms via `save_timetable`.
        """
        if not get_settings().enable_timetable_parsing:
            raise RuntimeError(
                "Automatic timetable parsing is disabled (ENABLE_TIMETABLE_PARSING)."
            )

        result = self.parser.parse(content=content, mime_type=content_type)
        upload = self._store_and_record(
            user_id=user_id,
            filename=filename,
            content=content,
            content_type=content_type,
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

    def save_timetable(
        self, *, user_id: uuid.UUID, subjects: list[SubjectInput]
    ) -> TimetableOut:
        """Persist the user-confirmed timetable, replacing any existing one.

        Preserved for V2 (parse → confirm → save). Clears the user's current
        subjects (cascading to slots) and recreates from the confirmed data.
        """
        for existing in self.subjects.list_for_user(user_id):
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

    def get_timetable(self, *, user_id: uuid.UUID) -> TimetableOut:
        """The user's saved subjects with their slots (empty if none). Preserved
        for V2; V1 populates no subjects."""
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

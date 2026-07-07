"""Timetable endpoints.

V1 (storage-only) — the active flow (Docs/03_System_Architecture.md §11, V1):
  POST   /timetable/upload  -> store the file, return its reference. No AI.
  GET    /timetable         -> current file reference + signed view URL
  DELETE /timetable         -> remove the stored file

Preserved for V2 (automatic parsing, gated by ENABLE_TIMETABLE_PARSING):
  POST /timetable/parse     -> store + parse -> editable preview
  POST /timetable/confirm   -> save confirmed subjects + slots
  GET  /timetable/subjects  -> read saved subjects + slots

Every request is authenticated and scoped to the current user; the user id comes
from the verified JWT, never from the client (Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.core.config import get_settings
from app.database.session import get_db
from app.schemas.timetable import (
    TimetableFile,
    TimetableFileState,
    TimetableOut,
    TimetablePreview,
    TimetableSaveRequest,
)
from app.services.storage_service import ALLOWED_MIME_TYPES, StorageError
from app.services.timetable_service import TimetableService

router = APIRouter(prefix="/timetable", tags=["timetable"])

DbDep = Annotated[Session, Depends(get_db)]


async def _read_valid_upload(file: UploadFile) -> tuple[bytes, str]:
    """Validate the upload's type/size and return (content, content_type)."""
    settings = get_settings()

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Upload a PDF, PNG, or JPG.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum size is 10 MB.",
        )
    return content, content_type


# =====================================================================
# V1 — storage-only
# =====================================================================


@router.post("/upload", response_model=TimetableFile)
async def upload_timetable(
    current_user: CurrentUserDep,
    db: DbDep,
    file: Annotated[UploadFile, File(...)],
) -> TimetableFile:
    """Upload a PDF/PNG/JPG timetable and store it. No parsing, no AI — the file
    is saved and its reference returned so it can be displayed immediately."""
    content, content_type = await _read_valid_upload(file)

    user_id = uuid.UUID(current_user.id)
    try:
        return TimetableService(db).upload_file(
            user_id=user_id,
            filename=file.filename or "timetable",
            content=content,
            content_type=content_type,
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not store the upload: {exc}",
        ) from exc


@router.get("", response_model=TimetableFileState)
def get_timetable_file(current_user: CurrentUserDep, db: DbDep) -> TimetableFileState:
    """Return the user's uploaded timetable file reference (with a view URL)."""
    user_id = uuid.UUID(current_user.id)
    return TimetableService(db).get_file(user_id=user_id)


@router.delete("", status_code=status.HTTP_200_OK)
def delete_timetable_file(
    current_user: CurrentUserDep, db: DbDep
) -> dict[str, bool]:
    """Delete the user's uploaded timetable file. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    removed = TimetableService(db).delete_file(user_id=user_id)
    return {"success": True, "removed": removed}


# =====================================================================
# V2 — automatic parsing (preserved; returns 404 while disabled)
# =====================================================================


def _require_parsing_enabled() -> None:
    if not get_settings().enable_timetable_parsing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automatic timetable parsing is not available in this version.",
        )


@router.post("/parse", response_model=TimetablePreview)
async def parse_timetable(
    current_user: CurrentUserDep,
    db: DbDep,
    file: Annotated[UploadFile, File(...)],
) -> TimetablePreview:
    """V2: upload + parse into an editable preview. Disabled in V1."""
    _require_parsing_enabled()
    content, content_type = await _read_valid_upload(file)
    user_id = uuid.UUID(current_user.id)
    try:
        return TimetableService(db).upload_and_parse(
            user_id=user_id,
            filename=file.filename or "timetable",
            content=content,
            content_type=content_type,
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not store the upload: {exc}",
        ) from exc


@router.post("/confirm", response_model=TimetableOut)
def confirm_timetable(
    payload: TimetableSaveRequest, current_user: CurrentUserDep, db: DbDep
) -> TimetableOut:
    """V2: persist the user-confirmed timetable. Disabled in V1."""
    _require_parsing_enabled()
    user_id = uuid.UUID(current_user.id)
    return TimetableService(db).save_timetable(
        user_id=user_id, subjects=payload.subjects
    )


@router.get("/subjects", response_model=TimetableOut)
def get_saved_subjects(current_user: CurrentUserDep, db: DbDep) -> TimetableOut:
    """V2: read saved subjects + slots. Disabled in V1."""
    _require_parsing_enabled()
    user_id = uuid.UUID(current_user.id)
    return TimetableService(db).get_timetable(user_id=user_id)

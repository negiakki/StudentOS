"""Timetable endpoints (Phase 4).

Flow (Docs/03_System_Architecture.md §11):
  POST /timetable/upload  -> store + parse, return an editable preview
  POST /timetable         -> save the user-confirmed timetable
  GET  /timetable         -> read the saved timetable

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
from app.schemas.timetable import TimetableOut, TimetablePreview, TimetableSaveRequest
from app.services.storage_service import ALLOWED_MIME_TYPES, StorageError
from app.services.timetable_service import TimetableService

router = APIRouter(prefix="/timetable", tags=["timetable"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post("/upload", response_model=TimetablePreview)
async def upload_timetable(
    current_user: CurrentUserDep,
    db: DbDep,
    file: Annotated[UploadFile, File(...)],
) -> TimetablePreview:
    """Upload a PDF/PNG/JPG timetable, parse it, and return a preview to confirm.

    Nothing academic is saved yet — the user reviews/edits the preview and posts
    it back to `POST /timetable`.
    """
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


@router.post("", response_model=TimetableOut)
def save_timetable(
    payload: TimetableSaveRequest, current_user: CurrentUserDep, db: DbDep
) -> TimetableOut:
    """Persist the user-confirmed timetable, replacing any existing one."""
    user_id = uuid.UUID(current_user.id)
    return TimetableService(db).save_timetable(
        user_id=user_id, subjects=payload.subjects
    )


@router.get("", response_model=TimetableOut)
def get_timetable(current_user: CurrentUserDep, db: DbDep) -> TimetableOut:
    """Return the current user's saved timetable (empty if none yet)."""
    user_id = uuid.UUID(current_user.id)
    return TimetableService(db).get_timetable(user_id=user_id)

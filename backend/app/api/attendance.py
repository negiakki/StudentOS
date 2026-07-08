"""Attendance endpoints (Phase 5 — manual attendance).

V1 lets the user manage their semester subjects and attended/total counts; the
backend computes percentage, safe-skips, and the threshold warning. Daily marking
and the calendar are Phase 6. Every request is scoped to the authenticated user
(Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.attendance import (
    AttendanceOverview,
    SubjectAttendance,
    SubjectCreate,
    SubjectUpdate,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["attendance"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/overview", response_model=AttendanceOverview)
def get_overview(current_user: CurrentUserDep, db: DbDep) -> AttendanceOverview:
    """Aggregate attendance across the user's subjects, for the dashboard."""
    user_id = uuid.UUID(current_user.id)
    return AttendanceService(db).overview(user_id=user_id)


@router.get("/subjects", response_model=list[SubjectAttendance])
def list_subjects(
    current_user: CurrentUserDep, db: DbDep
) -> list[SubjectAttendance]:
    """List the user's subjects with computed attendance."""
    user_id = uuid.UUID(current_user.id)
    return AttendanceService(db).list_subjects(user_id=user_id)


@router.post(
    "/subjects",
    response_model=SubjectAttendance,
    status_code=status.HTTP_201_CREATED,
)
def add_subject(
    payload: SubjectCreate, current_user: CurrentUserDep, db: DbDep
) -> SubjectAttendance:
    """Add a subject with its initial attended / total counts."""
    user_id = uuid.UUID(current_user.id)
    return AttendanceService(db).add_subject(user_id=user_id, payload=payload)


@router.patch("/subjects/{subject_id}", response_model=SubjectAttendance)
def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> SubjectAttendance:
    """Edit a subject's name or counts."""
    user_id = uuid.UUID(current_user.id)
    updated = AttendanceService(db).update_subject(
        user_id=user_id, subject_id=subject_id, payload=payload
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )
    return updated


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_200_OK)
def delete_subject(
    subject_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> dict[str, bool]:
    """Delete a subject and its attendance summary. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    removed = AttendanceService(db).delete_subject(
        user_id=user_id, subject_id=subject_id
    )
    return {"success": True, "removed": removed}

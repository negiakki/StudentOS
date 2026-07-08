"""Attendance endpoints (Phase 5 setup + Phase 6 daily marking).

Setup lets the user manage their semester subjects and attended/total baseline;
Phase 6 adds day-by-day marking (present/absent), edit-previous-days, the calendar
range, and the history list. The backend always computes percentage, safe-skips,
and the threshold warning. Every request is scoped to the authenticated user
(Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.attendance import (
    AttendanceOverview,
    AttendanceRecordOut,
    RecordMutationResult,
    RecordUpsert,
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


# --- Phase 6: daily marking, calendar, history -------------------------------


@router.get("/subjects/{subject_id}", response_model=SubjectAttendance)
def get_subject(
    subject_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> SubjectAttendance:
    """A single subject's computed attendance (for its detail page)."""
    user_id = uuid.UUID(current_user.id)
    subject = AttendanceService(db).get_subject(
        user_id=user_id, subject_id=subject_id
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )
    return subject


@router.get(
    "/subjects/{subject_id}/records", response_model=list[AttendanceRecordOut]
)
def list_records(
    subject_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    start: date | None = None,
    end: date | None = None,
    limit: int | None = None,
) -> list[AttendanceRecordOut]:
    """Records for the calendar (``start``+``end`` range) or, absent a range, the
    most recent ``limit`` records for the history list. Same underlying data."""
    user_id = uuid.UUID(current_user.id)
    records = AttendanceService(db).list_records(
        user_id=user_id, subject_id=subject_id, start=start, end=end, limit=limit
    )
    if records is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )
    return records


@router.put(
    "/subjects/{subject_id}/records/{attendance_date}",
    response_model=RecordMutationResult,
)
def mark_record(
    subject_id: uuid.UUID,
    attendance_date: date,
    payload: RecordUpsert,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RecordMutationResult:
    """Mark present/absent (or edit a previous day) for one date."""
    user_id = uuid.UUID(current_user.id)
    result = AttendanceService(db).mark(
        user_id=user_id,
        subject_id=subject_id,
        on_date=attendance_date,
        status=payload.status,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )
    subject, record = result
    return RecordMutationResult(subject=subject, record=record)


@router.delete(
    "/subjects/{subject_id}/records/{attendance_date}",
    response_model=RecordMutationResult,
)
def clear_record(
    subject_id: uuid.UUID,
    attendance_date: date,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RecordMutationResult:
    """Clear a day's mark, reversing its effect on the totals. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    subject = AttendanceService(db).unmark(
        user_id=user_id, subject_id=subject_id, on_date=attendance_date
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )
    return RecordMutationResult(subject=subject, record=None)

"""Assignment endpoints (Phase 7).

Standard CRUD plus a dashboard endpoint that groups PENDING assignments into
Today / Upcoming / Overdue. Every request is scoped to the authenticated user
(Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentDashboard,
    AssignmentOut,
    AssignmentUpdate,
)
from app.services.assignment_service import AssignmentService, InvalidSubjectError

router = APIRouter(prefix="/assignments", tags=["assignments"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/dashboard", response_model=AssignmentDashboard)
def get_dashboard(current_user: CurrentUserDep, db: DbDep) -> AssignmentDashboard:
    """Pending assignments grouped into Today / Upcoming / Overdue."""
    user_id = uuid.UUID(current_user.id)
    return AssignmentService(db).dashboard(user_id=user_id)


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    current_user: CurrentUserDep, db: DbDep
) -> list[AssignmentOut]:
    """List the user's assignments, soonest due date first."""
    user_id = uuid.UUID(current_user.id)
    return AssignmentService(db).list(user_id=user_id)


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate, current_user: CurrentUserDep, db: DbDep
) -> AssignmentOut:
    """Create an assignment. Always starts PENDING."""
    user_id = uuid.UUID(current_user.id)
    try:
        return AssignmentService(db).create(user_id=user_id, payload=payload)
    except InvalidSubjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> AssignmentOut:
    """A single assignment."""
    user_id = uuid.UUID(current_user.id)
    assignment = AssignmentService(db).get(
        user_id=user_id, assignment_id=assignment_id
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found."
        )
    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: uuid.UUID,
    payload: AssignmentUpdate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> AssignmentOut:
    """Edit an assignment, including marking it complete/pending."""
    user_id = uuid.UUID(current_user.id)
    try:
        updated = AssignmentService(db).update(
            user_id=user_id, assignment_id=assignment_id, payload=payload
        )
    except InvalidSubjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found."
        )
    return updated


@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
def delete_assignment(
    assignment_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> dict[str, bool]:
    """Delete an assignment. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    removed = AssignmentService(db).delete(
        user_id=user_id, assignment_id=assignment_id
    )
    return {"success": True, "removed": removed}

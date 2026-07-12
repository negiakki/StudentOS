"""Todo endpoints (Phase 8).

Standard CRUD plus a "today" endpoint that lists incomplete todos due today,
overdue, or undated. Every request is scoped to the authenticated user
(Docs/04_Database_Design.md §18).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.todo import TodoCreate, TodoOut, TodoUpdate
from app.services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/today", response_model=list[TodoOut])
def get_today(current_user: CurrentUserDep, db: DbDep) -> list[TodoOut]:
    """Incomplete todos due today, overdue, or undated."""
    user_id = uuid.UUID(current_user.id)
    return TodoService(db).today(user_id=user_id)


@router.get("", response_model=list[TodoOut])
def list_todos(current_user: CurrentUserDep, db: DbDep) -> list[TodoOut]:
    """List the user's todos, soonest due date first."""
    user_id = uuid.UUID(current_user.id)
    return TodoService(db).list(user_id=user_id)


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate, current_user: CurrentUserDep, db: DbDep
) -> TodoOut:
    """Create a todo. Always starts incomplete."""
    user_id = uuid.UUID(current_user.id)
    return TodoService(db).create(user_id=user_id, payload=payload)


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep) -> TodoOut:
    """A single todo."""
    user_id = uuid.UUID(current_user.id)
    todo = TodoService(db).get(user_id=user_id, todo_id=todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found."
        )
    return todo


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(
    todo_id: uuid.UUID,
    payload: TodoUpdate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> TodoOut:
    """Edit a todo, including marking it complete/incomplete."""
    user_id = uuid.UUID(current_user.id)
    updated = TodoService(db).update(user_id=user_id, todo_id=todo_id, payload=payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found."
        )
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_200_OK)
def delete_todo(
    todo_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> dict[str, bool]:
    """Delete a todo. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    removed = TodoService(db).delete(user_id=user_id, todo_id=todo_id)
    return {"success": True, "removed": removed}

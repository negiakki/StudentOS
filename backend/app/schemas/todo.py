"""Todo API schemas (Phase 8).

A todo is a simple checklist task, optionally due on a date
(Docs/04_Database_Design.md §10). Unlike assignments, completion is a plain
boolean rather than a status enum, and there's no subject link.
"""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Priority


class TodoCreate(BaseModel):
    """A new todo. `completed` always starts False."""

    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM


class TodoUpdate(BaseModel):
    """Partial edit of a todo, including marking it complete/incomplete."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_date: date | None = None
    priority: Priority | None = None
    completed: bool | None = None


class TodoOut(BaseModel):
    """A todo as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    completed: bool
    due_date: date | None
    priority: Priority

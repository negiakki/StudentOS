"""Coco chat API schemas (Docs/06_Coco_V1_Design.md §8).

`ChatIn`/`ChatOut` are the `/coco/chat` contract. Tool-argument models validate
call-1 output before any tool executes; write-payload models validate a
`PROPOSE_ACTION` before it is surfaced to the frontend (§6 structural safety).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AttendanceStatus, ChatRole, Priority

ActionType = Literal[
    "create_todo", "create_assignment", "complete_todo", "mark_attendance"
]


class ChatIn(BaseModel):
    """User's message to Coco. A null `conversation_id` starts a new conversation."""

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None


class ProposedAction(BaseModel):
    """A write Coco proposes. The frontend renders it as a confirmation card and,
    on Confirm, calls the existing REST endpoint — Coco never writes directly."""

    type: ActionType
    payload: dict[str, Any]
    summary: str


class ChatOut(BaseModel):
    """Coco's response to one message."""

    conversation_id: uuid.UUID
    reply: str
    proposed_action: ProposedAction | None = None
    coco_available: bool = True  # False → frontend shows the fallback line


class ChatHistoryMessage(BaseModel):
    """One persisted message, for reloading a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: ChatRole
    message: str
    created_at: datetime


class ChatHistoryOut(BaseModel):
    conversation_id: uuid.UUID
    messages: list[ChatHistoryMessage] = Field(default_factory=list)


# --- Tool argument models (validate call-1 args before executing) -------------


class GetSubjectAttendanceArgs(BaseModel):
    subject_name: str = Field(min_length=1, max_length=200)


class GetAttendanceRecordsArgs(BaseModel):
    subject_name: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=30, ge=1, le=30)


class GetAssignmentsArgs(BaseModel):
    filter: Literal["overdue", "due_today", "upcoming", "all"] | None = None


class GetTodosArgs(BaseModel):
    filter: Literal["today", "all"] | None = None


# --- Write-action payload models (validate a PROPOSE_ACTION) ------------------


class CreateTodoPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM


class CreateAssignmentPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    subject_name: str | None = None  # resolved to subject_id server-side
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM


class CompleteTodoPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)  # resolved to todo_id server-side


class MarkAttendancePayload(BaseModel):
    subject_name: str = Field(min_length=1, max_length=200)
    attendance_date: date
    status: AttendanceStatus

"""Timetable API schemas (Phase 4).

Two flows share these shapes:
- Upload → parse → *preview* (not persisted; the user reviews/edits it).
- *Confirm* the (possibly edited) preview → save subjects + slots.
"""

from __future__ import annotations

import uuid
from datetime import time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SlotInput(BaseModel):
    """One lecture in a confirmed timetable. `day_of_week` is 1 (Mon)..7 (Sun)."""

    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    room: str | None = None

    @model_validator(mode="after")
    def _end_after_start(self) -> "SlotInput":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SubjectInput(BaseModel):
    """A subject plus its lectures, as confirmed by the user before saving."""

    name: str = Field(min_length=1)
    faculty: str | None = None
    classroom: str | None = None
    slots: list[SlotInput] = Field(default_factory=list)


class TimetableSaveRequest(BaseModel):
    """User-confirmed timetable. Replaces any existing timetable for the user."""

    subjects: list[SubjectInput] = Field(default_factory=list)


# --- Preview (parse result, not yet persisted) ---


class SlotPreview(BaseModel):
    day_of_week: int
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    room: str | None = None


class SubjectPreview(BaseModel):
    name: str
    faculty: str | None = None
    classroom: str | None = None
    slots: list[SlotPreview] = Field(default_factory=list)


class TimetablePreview(BaseModel):
    """Result of parsing an upload. The frontend renders this for review/edit
    and posts back a TimetableSaveRequest to persist it."""

    file_id: uuid.UUID
    parsing_status: str
    parsing_confidence: Decimal | None = None
    parse_error: str | None = None
    subjects: list[SubjectPreview] = Field(default_factory=list)


# --- Saved timetable (read + confirmation responses) ---


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    room: str | None = None


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    faculty: str | None = None
    classroom: str | None = None
    slots: list[SlotOut] = Field(default_factory=list)


class TimetableOut(BaseModel):
    """The user's saved timetable: subjects each with their slots."""

    subjects: list[SubjectOut] = Field(default_factory=list)

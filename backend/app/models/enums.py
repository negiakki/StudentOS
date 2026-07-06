"""Enumerated column values (Docs/04_Database_Design.md)."""

from __future__ import annotations

import enum


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class FileCategory(str, enum.Enum):
    TIMETABLE = "TIMETABLE"


class ParsingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ChatRole(str, enum.Enum):
    USER = "USER"
    COCO = "COCO"

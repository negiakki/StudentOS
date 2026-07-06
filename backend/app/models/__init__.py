"""SQLAlchemy ORM models.

Importing this package registers every model on `Base.metadata`, which is what
Alembic autogenerate and `create_all` rely on. Import models from here.
"""

from app.database.base import Base
from app.models.academic import (
    AttendanceRecord,
    AttendanceSummary,
    Subject,
    TimetableSlot,
)
from app.models.enums import (
    AssignmentStatus,
    AttendanceStatus,
    ChatRole,
    FileCategory,
    ParsingStatus,
    Priority,
)
from app.models.planning import Assignment, Todo
from app.models.system import ChatMessage, Notification, UploadedFile
from app.models.user import Settings, User

__all__ = [
    "Base",
    "User",
    "Settings",
    "Subject",
    "TimetableSlot",
    "AttendanceSummary",
    "AttendanceRecord",
    "Assignment",
    "Todo",
    "UploadedFile",
    "Notification",
    "ChatMessage",
    "AttendanceStatus",
    "Priority",
    "AssignmentStatus",
    "FileCategory",
    "ParsingStatus",
    "ChatRole",
]

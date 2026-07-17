"""Coco tool registry and handlers (Docs/06_Coco_V1_Design.md §4, §5).

Every tool is a thin, read-only adapter over an existing service — no new
business logic. Handlers receive the request session and the authenticated
user's id (from the JWT, never from model output) and return compact JSON:
short keys, ISO dates, capped list sizes with a `truncated` flag.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Callable, TypedDict

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.repositories.timetable_repository import (
    SubjectRepository,
    UploadedFileRepository,
)
from app.schemas.assignment import AssignmentOut
from app.schemas.attendance import SubjectAttendance
from app.schemas.coco import (
    GetAssignmentsArgs,
    GetAttendanceRecordsArgs,
    GetSubjectAttendanceArgs,
    GetTodosArgs,
)
from app.schemas.todo import TodoOut
from app.services.assignment_service import AssignmentService
from app.services.attendance_service import AttendanceService
from app.services.todo_service import TodoService

# Result-size caps (§5 token minimization).
ASSIGNMENTS_CAP = 10
TODOS_CAP = 15


def match_subject(
    subjects: list[SubjectAttendance], name: str
) -> SubjectAttendance | None:
    """Resolve a spoken subject name ("dbms") to one tracked subject.

    Exact (case-insensitive) match wins; otherwise a substring match either way
    — but only when it is unambiguous. Ambiguity returns None so Coco asks a
    follow-up instead of guessing (§6)."""
    wanted = name.strip().lower()
    if not wanted:
        return None
    exact = [s for s in subjects if s.name.lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    partial = [
        s
        for s in subjects
        if wanted in s.name.lower() or s.name.lower() in wanted
    ]
    if len(partial) == 1:
        return partial[0]
    return None


def _subject_figures(s: SubjectAttendance) -> dict[str, Any]:
    return {
        "name": s.name,
        "attended": s.attended_classes,
        "total": s.total_classes,
        "pct": s.percentage,
        "safe_skips": s.safe_skips,
        "meets_threshold": s.meets_threshold,
    }


def _compact_assignment(a: AssignmentOut, subject_names: dict[uuid.UUID, str]) -> dict[str, Any]:
    out: dict[str, Any] = {"title": a.title, "priority": a.priority.value}
    if a.due_date:
        out["due"] = a.due_date.isoformat()
    if a.subject_id and a.subject_id in subject_names:
        out["subject"] = subject_names[a.subject_id]
    return out


def _compact_todo(t: TodoOut) -> dict[str, Any]:
    out: dict[str, Any] = {"title": t.title, "priority": t.priority.value}
    if t.due_date:
        out["due"] = t.due_date.isoformat()
    if t.completed:
        out["completed"] = True
    return out


def _capped(items: list[Any], cap: int) -> tuple[list[Any], bool]:
    return items[:cap], len(items) > cap


def _subject_name_map(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, str]:
    return {s.id: s.name for s in SubjectRepository(db).list_for_user(user_id)}


# --- Read tools ---------------------------------------------------------------


def get_attendance_overview(
    db: Session, user_id: uuid.UUID, args: BaseModel | None
) -> dict[str, Any]:
    overview = AttendanceService(db).overview(user_id=user_id)
    return {
        "overall_pct": overview.overall_percentage,
        "threshold": overview.threshold,
        "attended_total": overview.attended_total,
        "total_total": overview.total_total,
        "below_threshold_count": overview.below_threshold_count,
        "subjects": [_subject_figures(s) for s in overview.subjects],
    }


def get_subject_attendance(
    db: Session, user_id: uuid.UUID, args: GetSubjectAttendanceArgs
) -> dict[str, Any]:
    overview = AttendanceService(db).overview(user_id=user_id)
    matched = match_subject(overview.subjects, args.subject_name)
    if matched is None:
        return {
            "error": f"No unambiguous subject match for '{args.subject_name}'.",
            "known_subjects": [s.name for s in overview.subjects],
        }
    return {"threshold": overview.threshold, **_subject_figures(matched)}


def get_attendance_records(
    db: Session, user_id: uuid.UUID, args: GetAttendanceRecordsArgs
) -> dict[str, Any]:
    service = AttendanceService(db)
    subjects = service.list_subjects(user_id=user_id)
    matched = match_subject(subjects, args.subject_name)
    if matched is None:
        return {
            "error": f"No unambiguous subject match for '{args.subject_name}'.",
            "known_subjects": [s.name for s in subjects],
        }
    records = service.list_records(
        user_id=user_id, subject_id=matched.id, limit=args.limit
    )
    return {
        "subject": matched.name,
        "records": [
            {"date": r.attendance_date.isoformat(), "status": r.status.value}
            for r in (records or [])
        ],
    }


def get_assignments(
    db: Session, user_id: uuid.UUID, args: GetAssignmentsArgs
) -> dict[str, Any]:
    service = AssignmentService(db)
    subject_names = _subject_name_map(db, user_id)

    if args.filter == "all":
        items, truncated = _capped(service.list(user_id=user_id), ASSIGNMENTS_CAP)
        out: dict[str, Any] = {
            "all": [
                {**_compact_assignment(a, subject_names), "status": a.status.value}
                for a in items
            ]
        }
        if truncated:
            out["truncated"] = True
        return out

    dashboard = service.dashboard(user_id=user_id)
    groups = {
        "overdue": dashboard.overdue,
        "due_today": dashboard.today,
        "upcoming": dashboard.upcoming,
    }
    if args.filter:
        groups = {args.filter: groups[args.filter]}

    out = {}
    truncated_groups: list[str] = []
    for key, assignments in groups.items():
        items, truncated = _capped(assignments, ASSIGNMENTS_CAP)
        out[key] = [_compact_assignment(a, subject_names) for a in items]
        if truncated:
            truncated_groups.append(key)
    if truncated_groups:
        out["truncated"] = truncated_groups
    return out


def get_todos(
    db: Session, user_id: uuid.UUID, args: GetTodosArgs
) -> dict[str, Any]:
    service = TodoService(db)
    if args.filter == "today":
        todos = service.today(user_id=user_id)
    else:
        todos = [t for t in service.list(user_id=user_id) if not t.completed]
    items, truncated = _capped(todos, TODOS_CAP)
    out: dict[str, Any] = {"todos": [_compact_todo(t) for t in items]}
    if truncated:
        out["truncated"] = True
    return out


def get_daily_snapshot(
    db: Session, user_id: uuid.UUID, args: BaseModel | None
) -> dict[str, Any]:
    """Composed snapshot so "summarize my day" is one tool call, not an agent
    loop (§4): attendance warnings + assignment groups + today's todos."""
    overview = AttendanceService(db).overview(user_id=user_id)
    dashboard = AssignmentService(db).dashboard(user_id=user_id)
    todos = TodoService(db).today(user_id=user_id)
    subject_names = _subject_name_map(db, user_id)

    return {
        "attendance": {
            "overall_pct": overview.overall_percentage,
            "threshold": overview.threshold,
            "warnings": [
                _subject_figures(s)
                for s in overview.subjects
                if not s.meets_threshold
            ],
        },
        "assignments": {
            "overdue": [
                _compact_assignment(a, subject_names) for a in dashboard.overdue[:5]
            ],
            "due_today": [
                _compact_assignment(a, subject_names) for a in dashboard.today[:5]
            ],
            "upcoming_count": len(dashboard.upcoming),
        },
        "todos_today": [_compact_todo(t) for t in todos[:5]],
        "todos_today_count": len(todos),
    }


def get_timetable_status(
    db: Session, user_id: uuid.UUID, args: BaseModel | None
) -> dict[str, Any]:
    """Whether a timetable file is uploaded — never the file content (§5).

    Reads the metadata row directly rather than `TimetableService.get_file` so
    no signed storage URL is minted just to answer a yes/no question."""
    upload = UploadedFileRepository(db).get_timetable_for_user(user_id)
    if upload is None:
        return {"has_file": False}
    return {
        "has_file": True,
        "filename": upload.filename,
        "uploaded": upload.uploaded_at.date().isoformat(),
        "note": "Class timings are not parsed in V1; the user can view the file on the Timetable page.",
    }


# --- Registry -----------------------------------------------------------------


class ToolSpec(TypedDict):
    description: str
    args: str  # shown in the call-1 catalog
    args_model: type[BaseModel] | None
    handler: Callable[[Session, uuid.UUID, Any], dict[str, Any]]


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "get_attendance_overview": {
        "description": "Overall attendance: percentage, threshold, every subject's figures and safe skips",
        "args": "{}",
        "args_model": None,
        "handler": get_attendance_overview,
    },
    "get_subject_attendance": {
        "description": "One subject's attendance figures and safe skips (use for 'can I skip X?')",
        "args": '{"subject_name": string}',
        "args_model": GetSubjectAttendanceArgs,
        "handler": get_subject_attendance,
    },
    "get_attendance_records": {
        "description": "Recent day-by-day present/absent records for one subject",
        "args": '{"subject_name": string, "limit"?: int}',
        "args_model": GetAttendanceRecordsArgs,
        "handler": get_attendance_records,
    },
    "get_assignments": {
        "description": "Assignments grouped overdue / due_today / upcoming (or all)",
        "args": '{"filter"?: "overdue"|"due_today"|"upcoming"|"all"}',
        "args_model": GetAssignmentsArgs,
        "handler": get_assignments,
    },
    "get_todos": {
        "description": "Open todos ('today' = due today, overdue, or undated)",
        "args": '{"filter"?: "today"|"all"}',
        "args_model": GetTodosArgs,
        "handler": get_todos,
    },
    "get_daily_snapshot": {
        "description": "One combined snapshot of attendance warnings + assignments + today's todos (use for 'summarize my day', 'what should I do first')",
        "args": "{}",
        "args_model": None,
        "handler": get_daily_snapshot,
    },
    "get_timetable_status": {
        "description": "Whether a timetable file is uploaded (V1 cannot read class timings)",
        "args": "{}",
        "args_model": None,
        "handler": get_timetable_status,
    },
}

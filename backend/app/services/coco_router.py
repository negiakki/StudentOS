"""Deterministic front-door router for Coco (LLM-cost reduction layer).

Before Coco's two-call LLM flow runs (Docs/06_Coco_V1_Design.md §8), every
message is classified into one of four lanes. Three of them never touch the
provider:

  L0  STATIC   — greetings / thanks / "what can you do" → canned reply. Also
                 the create-todo/assignment redirects: those writes left V1, so
                 chat points at the existing UI forms instead of proposing.
  L1  REFUSE   — out-of-scope (weather, coding, essays, medical…) → polite
                 redirect naming Coco's real capabilities.
  L2  DIRECT   — a request that an existing backend handler already answers
                 (attendance / assignments / todos / timetable / dashboard):
                 run that handler and render a template. No LLM.
  L3  AI       — everything genuinely needing reasoning, plus the existing
                 write-intent → PROPOSE_ACTION flow. Falls through to the
                 unchanged two-call flow in ``CocoService``.

Design constraints honored here:
  * This is keyword + finite-set matching, NOT a natural-language parser — no
    grammar, no entity extraction beyond testing the user's OWN subject names
    for membership in the message (the "finite known-subject scan").
  * L2 handlers are the exact tools from ``coco_tools`` — no new business logic.
  * Ordering is strict L0 → L1 → L2 → L3; write intents and reasoning verbs are
    routed to L3 *before* L2 so "mark attendance" or "summarize my dashboard"
    are never mistaken for a direct lookup.
  * When a lane is uncertain, we fall through to L3 rather than guess — a wrong
    refusal or a guessed subject is worse than one extra LLM call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# --- Route types --------------------------------------------------------------


@dataclass
class StaticRoute:
    """L0 — a fixed reply; the provider is never called."""

    reply: str
    label: str = "STATIC"


@dataclass
class RefuseRoute:
    """L1 — out-of-scope; polite refusal, provider never called."""

    reply: str
    label: str = "REFUSE"


@dataclass
class DirectRoute:
    """L2 — run one existing tool and render a template. No provider call.

    ``tool_name``/``tool_args`` feed the existing ``CocoService._execute_tool``
    (same Pydantic validation and per-tool error handling as the LLM path);
    ``formatter`` turns that tool's compact result dict into the reply text.
    """

    label: str  # e.g. "DIRECT_ATTENDANCE" — used verbatim in the ROUTE log
    tool_name: str
    tool_args: dict[str, Any]
    formatter: Callable[[dict[str, Any]], str]


@dataclass
class AiRoute:
    """L3 — hand off to the existing two-call LLM flow. The concrete label
    (AI_SUMMARY vs AI_PROPOSE_ACTION) is decided after the flow runs."""

    label: str = "AI"


Route = StaticRoute | RefuseRoute | DirectRoute | AiRoute


# --- Capability copy (shared by L0 help and L1 refuse) ------------------------

_CAP_BULLETS = (
    "• Attendance — overall %, a single subject, safe skips, and history\n"
    "• Assignments — what's overdue, due today, or upcoming\n"
    "• Todos — today's tasks or your full list\n"
    "• Timetable — whether your timetable is uploaded\n"
    "• Daily summary — say “summarize my day” and I'll pull it together\n"
    "I can also mark your attendance or tick a todo off your list for you to confirm."
)

_HELP_REPLY = "I'm Coco, your StudentOS assistant. Here's what I can help with:\n\n" + _CAP_BULLETS

_GREETING_REPLY = (
    "Hey! \U0001f44b I'm Coco. Ask me about your attendance, assignments, or todos "
    "— or say “summarize my day”."
)

_THANKS_REPLY = "Anytime! Want me to check what's due or how your attendance is looking?"

_REFUSE_REPLY = (
    "That's outside what I do — I'm Coco, your StudentOS assistant, so I stick to "
    "your academics. Here's where I can actually help:\n\n" + _CAP_BULLETS
)


# --- L0 static ----------------------------------------------------------------

# Whole-message matches only (after stripping trailing punctuation). Deliberately
# tight: "help me create a todo" must NOT match "help".
_GREETINGS = {"hi", "hello", "hey", "yo", "hii", "heya", "hey coco", "hello coco", "hi coco"}
_THANKS = {"thanks", "thank you", "thanks!", "ty", "thx", "thank you coco", "thanks coco"}
_HELP = {"help", "what can you do", "what can you do?", "who are you", "what do you do", "what are you"}


# --- L1 out-of-scope ----------------------------------------------------------

# An out-of-scope signal triggers a refusal ONLY when no StudentOS signal is also
# present, so "help me with my attendance essay-style summary" is not refused.
_OUT_OF_SCOPE = (
    "weather", "temperature", "forecast", "rain today", "essay", "poem", "translate",
    "translation", "leetcode", "algorithm", "compile", "syntax error", "recipe",
    "news", "headline", "stock", "cricket", "football", "nba", "match score",
    "movie", "song", "lyrics", "joke", "medical", "medicine", "symptom", "diagnos",
    "depress", "anxiety", "suicide", "therapy", "president", "election",
    "capital of", "current events", "flight", "hotel", "restaurant", "write an email",
    "write me an email", "who won", "what year", "meaning of life",
)

_STUDENTOS_SIGNAL = (
    "attendance", "attend", "present", "absent", "skip", "assignment", "homework",
    "due", "deadline", "submit", "todo", "to-do", "to do", "task", "timetable",
    "time table", "class", "schedule", "subject", "dashboard", "semester",
)


# --- L3 write intents (route to the existing PROPOSE_ACTION flow) -------------
# V1 keeps exactly two conversational writes: mark attendance and complete a
# todo. Each is matched by intent signal, NOT one contiguous phrase, so a subject
# or todo name sitting mid-sentence ("mark DBMS present", "complete Guitar todo")
# is still seen as a write and reaches the propose flow instead of an L2 read.

_ATTENDANCE_STATE = ("present", "absent", "attendance")
# Imperative logging phrases — unambiguous anywhere in the message.
_ATT_WRITE_PHRASES = ("log my attendance", "log attendance", "mark my attendance")
# First-person reports. Matched only at the START of the message so a question
# ("how many classes have I attended?") — which contains "i attended" mid-string
# — is NOT mistaken for a statement to record, and stays an L2 read.
_ATT_WRITE_STATEMENTS = (
    "i attended", "i was present", "i was absent", "i missed", "i skipped",
)

_TODO_WORDS = ("todo", "to-do", "to do", "task")
_DONE_VERBS = ("complete", "finish", "tick off", "check off", "cross off")
_DONE_STATES = ("as done", "as complete", "as completed", "is done")


def _is_attendance_write(msg: str, stripped: str) -> bool:
    # "mark <subject> present/absent" / "mark today's <subject> attendance".
    if "mark" in msg and _has(msg, _ATTENDANCE_STATE):
        return True
    if _has(msg, _ATT_WRITE_PHRASES):
        return True
    return stripped.startswith(_ATT_WRITE_STATEMENTS)


def _is_todo_complete(msg: str) -> bool:
    if _has(msg, _DONE_VERBS) and _has(msg, _TODO_WORDS):
        return True
    return _has(msg, _DONE_STATES)  # "mark <todo> as done"


# --- L3 removed writes (create todo/assignment → point at the existing form) --
# V1 scope change: chat no longer creates todos/assignments — the UI forms are
# faster for the many required fields. A fixed reply redirects, with no provider
# call and no proposed_action.

_CREATE_VERBS = ("create", "add ", "new ", "make a", "make me a", "note down", "jot down")
_ASSIGNMENT_WORDS = ("assignment", "homework")

_CREATE_ASSIGNMENT_REDIRECT = (
    "Assignments are best created using the Add Assignment form so you can quickly "
    "fill in all the required details."
)
_CREATE_TODO_REDIRECT = (
    "Todos are best added using the Add Todo form so you can quickly fill in all the details."
)


# --- L3 reasoning verbs (a summary/judgement the LLM should handle) -----------

_REASONING = (
    "summar", "priorit", "what should i", "what do i need", "focus on", "interpret",
    "analy", "recommend", "advis", "advice", "plan my", "help me plan", "overwhelm",
    "where do i start", "where should i start", "most important", "what matters",
)


# --- keyword helpers ----------------------------------------------------------


def _has(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _normalize_exact(message: str) -> str:
    return message.strip().lower().strip("!.?, ")


# --- classifier ---------------------------------------------------------------


def classify(message: str, subjects_provider: Callable[[], list[str]]) -> Route:
    """Pick a lane for ``message``.

    ``subjects_provider`` returns the user's tracked subject names; it is called
    at most once, and only when an attendance intent needs the finite-set scan
    (so a "hi" never triggers a DB read).
    """
    exact = _normalize_exact(message)
    stripped = message.strip().lower()
    msg = " " + stripped + " "  # padded for loose substring tests

    # L0 — static replies (whole-message only) --------------------------------
    if exact in _GREETINGS:
        return StaticRoute(_GREETING_REPLY)
    if exact in _THANKS:
        return StaticRoute(_THANKS_REPLY)
    if exact in _HELP:
        return StaticRoute(_HELP_REPLY)

    # L1 — out-of-scope (only when nothing StudentOS is mentioned) -------------
    if _has(msg, _OUT_OF_SCOPE) and not _has(msg, _STUDENTOS_SIGNAL):
        return RefuseRoute(_REFUSE_REPLY)

    # L1.5 — create todo/assignment left V1: redirect to the form, no LLM. Comes
    # before the write-intent check so "add a todo" redirects instead of routing
    # to a (now-removed) create proposal. Assignment tested before todo because
    # "add an assignment todo item"-style phrasing shouldn't shadow assignments.
    if _has(msg, _CREATE_VERBS):
        if _has(msg, _ASSIGNMENT_WORDS):
            return StaticRoute(_CREATE_ASSIGNMENT_REDIRECT, label="REDIRECT_CREATE_ASSIGNMENT")
        if _has(msg, _TODO_WORDS):
            return StaticRoute(_CREATE_TODO_REDIRECT, label="REDIRECT_CREATE_TODO")

    # L3 (early) — the two kept writes (mark attendance / complete todo) keep the
    # existing PROPOSE_ACTION flow. Checked before L2 so "mark DBMS present" or
    # "complete Guitar todo" isn't captured as a direct attendance/todo read.
    if _is_attendance_write(msg, stripped) or _is_todo_complete(msg):
        return AiRoute()

    # L3 (early) — reasoning/summary verbs go to the LLM, not a template.
    if _has(msg, _REASONING):
        return AiRoute()

    # L2 — direct backend capabilities (first bucket to match wins) ------------
    direct = (
        _route_attendance(msg, subjects_provider)
        or _route_assignments(msg)
        or _route_todos(msg)
        or _route_timetable(msg)
        or _route_dashboard(msg)
    )
    if direct is not None:
        return direct

    # L3 — default: genuine reasoning / anything we couldn't resolve safely.
    return AiRoute()


def _route_attendance(
    msg: str, subjects_provider: Callable[[], list[str]]
) -> DirectRoute | None:
    if not _has(msg, ("attendance", "attend", "safe skip", "can i skip", "present", "absent", "classes have i")):
        return None

    # Finite known-subject scan: does one of the user's OWN subject names appear?
    subjects = subjects_provider()
    matched = [name for name in subjects if name.lower() in msg]

    if len(matched) == 1 and _has(msg, ("history", "record", "log", "present on", "absent on", "past few", "last few")):
        return DirectRoute(
            "DIRECT_ATTENDANCE",
            "get_attendance_records",
            {"subject_name": matched[0]},
            _fmt_attendance_records,
        )
    if len(matched) == 1:
        return DirectRoute(
            "DIRECT_ATTENDANCE",
            "get_subject_attendance",
            {"subject_name": matched[0]},
            _fmt_subject_attendance,
        )
    # No single subject (overall / safe-skips / ambiguous) → overview template.
    return DirectRoute(
        "DIRECT_ATTENDANCE", "get_attendance_overview", {}, _fmt_attendance_overview
    )


def _route_assignments(msg: str) -> DirectRoute | None:
    if not _has(msg, ("assignment", "homework", " hw ", "deadline")):
        return None
    if _has(msg, ("overdue", "late", "missed", "past due")):
        args = {"filter": "overdue"}
    elif _has(msg, ("upcoming", "this week", "next week", "coming up", "soon")):
        args = {"filter": "upcoming"}
    elif _has(msg, ("today", "due today")):
        args = {"filter": "due_today"}
    elif _has(msg, ("all ", "everything", "every assignment", "full list", "list")):
        args = {"filter": "all"}
    else:
        args = {}  # dashboard grouping (overdue + due today + upcoming)
    return DirectRoute("DIRECT_ASSIGNMENTS", "get_assignments", args, _fmt_assignments)


def _route_todos(msg: str) -> DirectRoute | None:
    if not _has(msg, ("todo", "to-do", "to do", " task", "checklist")):
        return None
    if _has(msg, ("all ", "everything", "full list", "every task")):
        args = {"filter": "all"}
    else:
        args = {"filter": "today"}
    return DirectRoute("DIRECT_TODOS", "get_todos", args, _fmt_todos)


def _route_timetable(msg: str) -> DirectRoute | None:
    if not _has(msg, ("timetable", "time table", "next class", "class today", "classes today", "my schedule", "what class")):
        return None
    return DirectRoute("DIRECT_TIMETABLE", "get_timetable_status", {}, _fmt_timetable)


def _route_dashboard(msg: str) -> DirectRoute | None:
    if not _has(msg, ("dashboard", "my stats", "statistics", "overview of everything", "everything today")):
        return None
    return DirectRoute("DIRECT_DASHBOARD", "get_daily_snapshot", {}, _fmt_daily_snapshot)


# --- template formatters (pure dict → str; never call the provider) -----------

_ATTENDANCE_FALLBACK = "I couldn't pull that up just now — you can view it on the Attendance page."


def _fmt_attendance_overview(r: dict[str, Any]) -> str:
    if "error" in r:
        return _ATTENDANCE_FALLBACK
    lines = [f"You're at {r['overall_pct']}% attendance overall (threshold {r['threshold']}%)."]
    warnings = [s for s in r.get("subjects", []) if not s["meets_threshold"]]
    if warnings:
        names = ", ".join(f"{s['name']} ({s['pct']}%)" for s in warnings)
        lines.append(f"⚠️ Below threshold: {names}.")
    else:
        lines.append("Every subject is above threshold. \U0001f389")
    return " ".join(lines)


def _fmt_subject_attendance(r: dict[str, Any]) -> str:
    if "error" in r:
        known = ", ".join(r.get("known_subjects", []))
        return f"I couldn't match that subject. You're tracking: {known}." if known else _ATTENDANCE_FALLBACK
    if r["meets_threshold"]:
        return (
            f"{r['name']}: {r['attended']}/{r['total']} classes ({r['pct']}%), "
            f"threshold {r['threshold']}%. You can safely skip {r['safe_skips']} more."
        )
    return (
        f"{r['name']}: {r['attended']}/{r['total']} ({r['pct']}%) — below the "
        f"{r['threshold']}% threshold, so no safe skips right now."
    )


def _fmt_attendance_records(r: dict[str, Any]) -> str:
    if "error" in r:
        return _ATTENDANCE_FALLBACK
    records = r.get("records", [])
    if not records:
        return f"No attendance records yet for {r['subject']}."
    shown = records[:10]
    body = "; ".join(f"{x['date']}: {x['status']}" for x in shown)
    more = f" (+{len(records) - 10} more)" if len(records) > 10 else ""
    return f"{r['subject']} — {body}{more}."


def _fmt_assignments(r: dict[str, Any]) -> str:
    if "error" in r:
        return "I couldn't load your assignments just now — check the Assignments page."

    def render(items: list[dict[str, Any]]) -> str:
        return ", ".join(a["title"] + (f" (due {a['due']})" if a.get("due") else "") for a in items)

    if "all" in r:
        if not r["all"]:
            return "You have no assignments yet."
        tail = "…" if r.get("truncated") else ""
        return f"All assignments: {render(r['all'])}{tail}."

    parts = []
    for key, label in (("overdue", "Overdue"), ("due_today", "Due today"), ("upcoming", "Upcoming")):
        if r.get(key):
            parts.append(f"{label}: {render(r[key])}")
    if not parts:
        return "Nothing due — you're all caught up. ✅"
    return " | ".join(parts) + "."


def _fmt_todos(r: dict[str, Any]) -> str:
    if "error" in r:
        return "I couldn't load your todos just now — check the Todo page."
    todos = r.get("todos", [])
    if not todos:
        return "No open todos right now. ✅"
    body = ", ".join(t["title"] + (f" (due {t['due']})" if t.get("due") else "") for t in todos)
    tail = "…" if r.get("truncated") else ""
    return f"Your todos: {body}{tail}."


def _fmt_timetable(r: dict[str, Any]) -> str:
    if not r.get("has_file"):
        return "You haven't uploaded a timetable yet — add it on the Timetable page."
    name = r.get("filename", "your file")
    return (
        f"Your timetable ({name}) is uploaded. Heads up: I can't read class timings in "
        "V1 — open the Timetable page to see the slots."
    )


def _fmt_daily_snapshot(r: dict[str, Any]) -> str:
    att = r["attendance"]
    asg = r["assignments"]
    lines = [f"Attendance: {att['overall_pct']}% overall (threshold {att['threshold']}%)."]
    if att.get("warnings"):
        lines.append("⚠️ Watch: " + ", ".join(w["name"] for w in att["warnings"]) + ".")
    if asg.get("overdue"):
        lines.append("Overdue: " + ", ".join(a["title"] for a in asg["overdue"]) + ".")
    if asg.get("due_today"):
        lines.append("Due today: " + ", ".join(a["title"] for a in asg["due_today"]) + ".")
    if r.get("todos_today_count"):
        lines.append(f"Todos today: {r['todos_today_count']}.")
    if len(lines) == 1:
        lines.append("Nothing urgent — you're in good shape. ✅")
    return " ".join(lines)

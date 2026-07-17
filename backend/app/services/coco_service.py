"""Coco orchestrator (Docs/06_Coco_V1_Design.md §5, §8).

Two-call flow per message:
  1. Call 1 — tool selection: catalog-only prompt, strict JSON out, low temp.
  2. The one selected tool runs in Python (args Pydantic-validated first) through
     the existing user-scoped services.
  3. Call 2 — answering: identity prompt + TOOL_RESULT, normal temp. A
     `PROPOSE_ACTION:` trailer becomes a confirmation card; the write itself is
     executed by the frontend against the existing REST endpoints (§4).

Failures never raise to the API layer: provider trouble degrades to
`coco_available: false` with the mandated fallback line (Architecture §15).
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.interfaces.chat_provider import ChatMessage as ProviderMessage
from app.ai.interfaces.chat_provider import ChatRequest
from app.ai.routers.chat_router import get_chat_router
from app.models.enums import ChatRole
from app.models.system import ChatMessage
from app.models.user import User
from app.repositories.chat_repository import ChatMessageRepository
from app.schemas.coco import (
    ChatIn,
    ChatOut,
    CompleteTodoPayload,
    CreateAssignmentPayload,
    CreateTodoPayload,
    MarkAttendancePayload,
    ProposedAction,
)
from app.services.attendance_service import AttendanceService
from app.services.coco_tools import TOOL_REGISTRY, match_subject
from app.services.todo_service import TodoService

# CLAUDE.md-mandated fallback line (Design §6; Architecture §15).
FALLBACK_REPLY = "Coco is temporarily unavailable. Your StudentOS data is still available."

# Last 6 messages (3 turns) of the current conversation — context, not memory (§5).
CONTEXT_WINDOW = 6

_ACTION_MARKER = "PROPOSE_ACTION:"

_ACTION_PAYLOAD_MODELS = {
    "create_todo": CreateTodoPayload,
    "create_assignment": CreateAssignmentPayload,
    "complete_todo": CompleteTodoPayload,
    "mark_attendance": MarkAttendancePayload,
}

_SELECTION_PROMPT = """You are the tool selector for Coco, a student's academic assistant. Today is {today}.

Pick the ONE tool that best answers the user's latest message.

Tools:
{catalog}

Reply with strict JSON only — no prose, no code fences:
{{"tool": "<tool_name>", "args": {{...}}}}
or, if no tool fits (greetings, chitchat, questions about Coco itself, or a write request like creating a todo):
{{"tool": null}}

Rules:
- "summarize my day" / "what should I do first" -> get_daily_snapshot
- "can I skip <subject>?" -> get_subject_attendance
- attendance questions without a subject -> get_attendance_overview
- "was I present on <day>?" -> get_attendance_records
- class timings / next class -> get_timetable_status
- for write requests (add/complete a todo, add an assignment, mark attendance), select the tool whose data helps fill in the details (get_todos for completing a todo, get_attendance_overview for marking attendance), or null if none helps."""

_SELECTION_RETRY = "\n\nYour previous reply was not valid JSON. Reply with ONLY the JSON object this time."

_ANSWER_PROMPT = """You are Coco, the student's academic co-pilot inside StudentOS. Today is {today}. The student's name is {name}.

Personality: friendly and encouraging, like a helpful senior — never robotic, never lecturing. Answer in 1-3 sentences first; add detail only if useful. At most one emoji.

Grounding rules (most important):
- Every number, date, and fact you state must come from TOOL_RESULT below. Never estimate, guess, or invent data.
- If TOOL_RESULT is NONE or has an "error", say plainly what you can't see and what you can help with instead.
- You cannot read class timings, grades, exams, syllabus content, or weather. Timetable parsing arrives in V2 — say so honestly when asked.
- You don't do coursework (essays, solutions) — you help manage it. Redirect in one line.
- No medical or mental-health advice: brief empathy, suggest talking to someone qualified.
- You cannot delete anything or bulk-edit — point to the relevant page.

Write actions: you may propose creating a todo, creating an assignment, completing a todo, or marking attendance — only when the user asked for it. The user will see a confirmation card before anything happens. To propose one, end your reply with a single line:
PROPOSE_ACTION: {{"type": "create_todo"|"create_assignment"|"complete_todo"|"mark_attendance", "payload": {{...}}, "summary": "<one-line description of the action>"}}

Payload fields — create_todo: title, due_date? (YYYY-MM-DD), priority? (LOW|MEDIUM|HIGH). create_assignment: title, description?, subject_name?, due_date?, priority?. complete_todo: title (of the existing todo). mark_attendance: subject_name, attendance_date (YYYY-MM-DD), status (PRESENT|ABSENT).
If a required field is missing or a reference is ambiguous, ask ONE follow-up question instead of proposing. Resolve relative dates ("tomorrow", "next Monday") from today's date.

TOOL_RESULT:
{tool_result}"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


class CocoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.messages = ChatMessageRepository(db)
        self.router = get_chat_router()

    # --- public API -----------------------------------------------------------

    def chat(self, *, user: User, payload: ChatIn) -> ChatOut:
        conversation_id = payload.conversation_id or uuid.uuid4()
        if not self.router.available:
            return self._unavailable(conversation_id)

        history = self.messages.list_recent(
            user.id, conversation_id, CONTEXT_WINDOW
        )

        selected = self._select_tool(payload.message, history)
        if selected is None:  # provider failed on call 1
            return self._unavailable(conversation_id)
        tool_name, tool_args = selected

        tool_result: dict[str, Any] | None = None
        if tool_name is not None:
            tool_result = self._execute_tool(user.id, tool_name, tool_args)

        reply = self._answer(user, payload.message, tool_result, history)
        if reply is None:  # provider failed on call 2; nothing to roll back (§8)
            return self._unavailable(conversation_id)

        reply_text, proposed_action = self._extract_action(user.id, reply)
        self._persist_exchange(
            user.id, conversation_id, payload.message, reply_text
        )

        return ChatOut(
            conversation_id=conversation_id,
            reply=reply_text,
            proposed_action=proposed_action,
            coco_available=True,
        )

    def get_history(
        self, *, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> list[ChatMessage]:
        """Full conversation, oldest first, for reloading the panel."""
        return self.messages.list_conversation(user_id, conversation_id)

    # --- call 1: tool selection -----------------------------------------------

    def _select_tool(
        self, user_message: str, history: list[ChatMessage]
    ) -> tuple[str | None, dict[str, Any]] | None:
        """Returns (tool, args); (None, {}) when no tool applies; None when the
        provider itself failed (→ fallback)."""
        catalog = "\n".join(
            f"- {name}: {spec['description']}. Args: {spec['args']}"
            for name, spec in TOOL_REGISTRY.items()
        )
        prompt = _SELECTION_PROMPT.format(
            today=date.today().isoformat(), catalog=catalog
        )

        for attempt in (prompt, prompt + _SELECTION_RETRY):
            result = self.router.complete(
                ChatRequest(
                    messages=self._with_history(attempt, history, user_message),
                    temperature=0.1,
                )
            )
            if not result.ok:
                return None
            try:
                parsed = json.loads(_strip_fences(result.text))
            except json.JSONDecodeError:
                continue  # one stricter retry (§8 failure table)
            if not isinstance(parsed, dict):
                continue
            tool = parsed.get("tool")
            args = parsed.get("args")
            if tool is not None and tool not in TOOL_REGISTRY:
                tool = None
            return tool, args if isinstance(args, dict) else {}

        # Malformed twice: answer without a tool rather than failing the chat.
        return None, {}

    # --- tool execution -------------------------------------------------------

    def _execute_tool(
        self, user_id: uuid.UUID, tool_name: str, tool_args: dict[str, Any]
    ) -> dict[str, Any]:
        spec = TOOL_REGISTRY[tool_name]
        args_model = spec["args_model"]
        try:
            args = args_model(**tool_args) if args_model else None
        except ValidationError:
            # Invalid args are never executed (§6); call 2 turns this into a
            # follow-up question.
            return {"error": f"Invalid arguments for {tool_name}; ask the user to clarify."}
        try:
            return spec["handler"](self.db, user_id, args)
        except Exception:  # one tool failing must not take Coco down (§8)
            return {"error": f"{tool_name} is having trouble right now."}

    # --- call 2: answering ----------------------------------------------------

    def _answer(
        self,
        user: User,
        user_message: str,
        tool_result: dict[str, Any] | None,
        history: list[ChatMessage],
    ) -> str | None:
        first_name = (user.full_name or "").strip().split(" ")[0] or "there"
        prompt = _ANSWER_PROMPT.format(
            today=date.today().isoformat(),
            name=first_name,
            tool_result=(
                json.dumps(tool_result, separators=(",", ":"))
                if tool_result is not None
                else "NONE"
            ),
        )
        result = self.router.complete(
            ChatRequest(
                messages=self._with_history(prompt, history, user_message),
                temperature=0.7,
            )
        )
        if not result.ok:
            return None
        return result.text.strip()

    # --- proposed actions -----------------------------------------------------

    def _extract_action(
        self, user_id: uuid.UUID, reply: str
    ) -> tuple[str, ProposedAction | None]:
        """Split a PROPOSE_ACTION trailer off the reply, validate it, and resolve
        name references to ids. Anything malformed or unresolvable is dropped —
        a misparse must never become a confirmation card (§6)."""
        if _ACTION_MARKER not in reply:
            return reply, None
        text, _, raw = reply.partition(_ACTION_MARKER)
        text = text.strip()
        try:
            data = json.loads(_strip_fences(raw))
            action_type = data["type"]
            model = _ACTION_PAYLOAD_MODELS[action_type]
            parsed = model(**data["payload"])
            summary = str(data["summary"])
        except (ValueError, KeyError, TypeError, ValidationError):
            return text, None

        payload = self._resolve_payload(user_id, action_type, parsed)
        if payload is None:
            return text, None
        return text, ProposedAction(type=action_type, payload=payload, summary=summary)

    def _resolve_payload(
        self, user_id: uuid.UUID, action_type: str, parsed: Any
    ) -> dict[str, Any] | None:
        """Turn model-supplied names into ids for the existing REST endpoints.
        Returns None when a reference doesn't resolve unambiguously."""
        if action_type == "create_todo":
            return parsed.model_dump(mode="json")

        if action_type == "create_assignment":
            payload = parsed.model_dump(mode="json", exclude={"subject_name"})
            payload["subject_id"] = None
            if parsed.subject_name:
                subjects = AttendanceService(self.db).list_subjects(user_id=user_id)
                matched = match_subject(subjects, parsed.subject_name)
                # An unmatched subject shouldn't block creating the assignment —
                # subject_id is optional on POST /assignments.
                payload["subject_id"] = str(matched.id) if matched else None
            return payload

        if action_type == "complete_todo":
            open_todos = [
                t
                for t in TodoService(self.db).list(user_id=user_id)
                if not t.completed
            ]
            wanted = parsed.title.strip().lower()
            matches = [t for t in open_todos if t.title.lower() == wanted] or [
                t for t in open_todos if wanted in t.title.lower()
            ]
            if len(matches) != 1:
                return None
            return {"todo_id": str(matches[0].id), "title": matches[0].title}

        if action_type == "mark_attendance":
            subjects = AttendanceService(self.db).list_subjects(user_id=user_id)
            matched = match_subject(subjects, parsed.subject_name)
            if matched is None:
                return None
            return {
                "subject_id": str(matched.id),
                "subject_name": matched.name,
                "attendance_date": parsed.attendance_date.isoformat(),
                "status": parsed.status.value,
            }

        return None

    # --- shared helpers -------------------------------------------------------

    def _with_history(
        self, system_prompt: str, history: list[ChatMessage], user_message: str
    ) -> list[ProviderMessage]:
        messages = [ProviderMessage(role="system", content=system_prompt)]
        for msg in history:  # text only; old tool results are never replayed (§5)
            messages.append(
                ProviderMessage(
                    role="user" if msg.role == ChatRole.USER else "assistant",
                    content=msg.message,
                )
            )
        messages.append(ProviderMessage(role="user", content=user_message))
        return messages

    def _persist_exchange(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        reply: str,
    ) -> None:
        # Stamped app-side: the column's `func.now()` default is per-transaction,
        # which would give every row of one exchange an identical created_at and
        # make chronological ordering depend on tie-breaks alone.
        self.messages.add(
            ChatMessage(
                user_id=user_id,
                conversation_id=conversation_id,
                role=ChatRole.USER,
                message=user_message,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.messages.add(
            ChatMessage(
                user_id=user_id,
                conversation_id=conversation_id,
                role=ChatRole.COCO,
                message=reply,
                created_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _unavailable(conversation_id: uuid.UUID) -> ChatOut:
        return ChatOut(
            conversation_id=conversation_id,
            reply=FALLBACK_REPLY,
            coco_available=False,
        )

"""Tests for Coco's deterministic routing layer (LLM-cost reduction).

Pure stdlib — ``unittest`` + ``unittest.mock``, no pytest, no new dependency,
no live database. A counting ``FakeRouter`` is injected into ``CocoService`` so
each test can assert exactly how many provider (LLM) calls a message triggers.

Run:  python -m unittest app.tests.test_coco_router
"""

from __future__ import annotations

import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest import mock

from app.ai.interfaces.chat_provider import ChatResult
from app.schemas.coco import ChatIn
from app.services import coco_service
from app.services.coco_service import CocoService


class FakeRouter:
    """Stand-in chat router that counts ``complete()`` calls and returns queued
    canned results — so a test can prove a route made zero provider calls."""

    def __init__(self, results: list[ChatResult] | None = None, available: bool = True):
        self._results = list(results or [])
        self.available = available
        self.calls = 0

    def complete(self, request):  # noqa: ARG002 — signature parity only
        self.calls += 1
        if self._results:
            return self._results.pop(0)
        return ChatResult(ok=True, text='{"tool": null}')


class _FakeUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.full_name = "Riya Sharma"


class _FakeMessageRepo:
    """No-DB replacement for ChatMessageRepository: records adds, no history."""

    def __init__(self, _db):
        self.added: list[object] = []
        self.pruned_before: object = None

    def list_recent(self, *_a, **_k):
        return []

    def add(self, obj):
        self.added.append(obj)
        return obj

    def delete_older_than(self, cutoff):
        self.pruned_before = cutoff
        return 0


class _FakeSession:
    """Minimal stand-in exposing only the SAVEPOINT context the cleanup uses."""

    @contextmanager
    def begin_nested(self):
        yield


# Representative tool outputs, so the L2 formatters run on real-shaped data
# without touching the services/DB.
_TOOL_RESULTS = {
    "get_attendance_overview": {
        "overall_pct": 82.0,
        "threshold": 75,
        "attended_total": 82,
        "total_total": 100,
        "below_threshold_count": 0,
        "subjects": [
            {"name": "DBMS", "attended": 40, "total": 50, "pct": 80.0, "safe_skips": 2, "meets_threshold": True},
        ],
    },
    "get_subject_attendance": {
        "threshold": 75, "name": "DBMS", "attended": 40, "total": 50,
        "pct": 80.0, "safe_skips": 2, "meets_threshold": True,
    },
    "get_assignments": {
        "overdue": [], "due_today": [{"title": "ER diagram", "priority": "HIGH"}], "upcoming": [],
    },
    "get_todos": {"todos": [{"title": "Read chapter 4", "priority": "MEDIUM"}]},
    "get_timetable_status": {"has_file": True, "filename": "sem5.pdf", "uploaded": "2026-07-01"},
    "get_daily_snapshot": {
        "attendance": {"overall_pct": 82.0, "threshold": 75, "warnings": []},
        "assignments": {"overdue": [], "due_today": [], "upcoming_count": 0},
        "todos_today": [], "todos_today_count": 0,
    },
}


class CocoRoutingTest(unittest.TestCase):
    def setUp(self):
        self.user = _FakeUser()
        # Patch the repo (no DB), the subject scan, and tool execution (no DB).
        patch_repo = mock.patch.object(coco_service, "ChatMessageRepository", _FakeMessageRepo)
        patch_subjects = mock.patch.object(
            CocoService, "_user_subject_names", lambda self, uid: ["DBMS", "Operating Systems"]
        )
        patch_exec = mock.patch.object(
            CocoService, "_execute_tool",
            lambda self, uid, name, args: dict(_TOOL_RESULTS[name]),
        )
        patch_repo.start(); patch_subjects.start(); patch_exec.start()
        self.addCleanup(patch_repo.stop)
        self.addCleanup(patch_subjects.stop)
        self.addCleanup(patch_exec.stop)

    def _chat(self, message: str, results=None):
        router = FakeRouter(results=results)
        service = CocoService(db=_FakeSession(), router=router)
        out = service.chat(user=self.user, payload=ChatIn(message=message))
        return out, router

    # --- L0 static: zero provider calls ---------------------------------------

    def test_greeting_makes_no_provider_call(self):
        for greeting in ("hi", "Hello", "hey!", "thanks", "what can you do?"):
            with self.subTest(greeting=greeting):
                out, router = self._chat(greeting)
                self.assertEqual(router.calls, 0)
                self.assertTrue(out.coco_available)
                self.assertIsNone(out.proposed_action)
                self.assertTrue(out.reply)

    # --- L1 refuse: zero provider calls ---------------------------------------

    def test_out_of_scope_makes_no_provider_call(self):
        for q in ("what's the weather today?", "write me an essay", "who won the cricket match", "translate this to French"):
            with self.subTest(q=q):
                out, router = self._chat(q)
                self.assertEqual(router.calls, 0)
                self.assertIn("StudentOS", out.reply)
                self.assertIsNone(out.proposed_action)

    # --- L2 direct: zero provider calls ---------------------------------------

    def test_attendance_overview_makes_no_provider_call(self):
        out, router = self._chat("what's my overall attendance?")
        self.assertEqual(router.calls, 0)
        self.assertIn("82", out.reply)
        self.assertIsNone(out.proposed_action)

    def test_subject_attendance_uses_finite_scan_no_provider_call(self):
        out, router = self._chat("can I skip DBMS?")
        self.assertEqual(router.calls, 0)
        self.assertIn("DBMS", out.reply)

    def test_assignments_makes_no_provider_call(self):
        out, router = self._chat("what assignments are due today?")
        self.assertEqual(router.calls, 0)
        self.assertIn("ER diagram", out.reply)
        self.assertIsNone(out.proposed_action)

    def test_todos_makes_no_provider_call(self):
        out, router = self._chat("show me today's tasks")
        self.assertEqual(router.calls, 0)
        self.assertIn("Read chapter 4", out.reply)

    # --- L3 AI: provider IS called --------------------------------------------

    def test_dashboard_summary_calls_provider(self):
        results = [
            ChatResult(ok=True, text='{"tool": null}'),          # call 1: selection
            ChatResult(ok=True, text="Here's your day at a glance: you're on track."),  # call 2
        ]
        out, router = self._chat("summarize my dashboard", results=results)
        self.assertGreaterEqual(router.calls, 1)
        self.assertIsNone(out.proposed_action)
        self.assertTrue(out.coco_available)

    def test_create_assignment_redirects_to_form_no_provider_call(self):
        # V1 scope change: creating an assignment left chat — it redirects to the
        # Add Assignment form deterministically, with no LLM call and no action.
        out, router = self._chat("create an assignment for my history essay due July 25")
        self.assertEqual(router.calls, 0)
        self.assertIsNone(out.proposed_action)
        self.assertIn("Add Assignment form", out.reply)

    def test_create_todo_redirects_to_form_no_provider_call(self):
        out, router = self._chat("add a todo to buy a lab notebook")
        self.assertEqual(router.calls, 0)
        self.assertIsNone(out.proposed_action)
        self.assertIn("Add Todo form", out.reply)

    def test_mark_attendance_with_subject_reaches_ai_and_proposes(self):
        # "mark DBMS present" must NOT be captured as an L2 attendance read — a
        # subject sitting mid-message still routes to the propose flow.
        results = [
            ChatResult(ok=True, text='{"tool": null}'),
            ChatResult(
                ok=True,
                text=(
                    "Marked!\n"
                    'PROPOSE_ACTION: {"type": "mark_attendance", '
                    '"payload": {"subject_name": "DBMS", "attendance_date": "2026-07-18", "status": "PRESENT"}, '
                    '"summary": "Mark DBMS present today"}'
                ),
            ),
        ]
        with mock.patch.object(
            CocoService, "_resolve_payload",
            lambda self, uid, atype, parsed: {
                "subject_id": "s1", "subject_name": "DBMS",
                "attendance_date": "2026-07-18", "status": "PRESENT",
            },
        ):
            out, router = self._chat("Mark DBMS present", results=results)
        self.assertGreaterEqual(router.calls, 1)
        self.assertIsNotNone(out.proposed_action)
        self.assertEqual(out.proposed_action.type, "mark_attendance")

    def test_complete_todo_with_name_reaches_ai_and_proposes(self):
        # "complete Guitar todo" must reach the propose flow, not an L2 todo read.
        results = [
            ChatResult(ok=True, text='{"tool": null}'),
            ChatResult(
                ok=True,
                text=(
                    "Done!\n"
                    'PROPOSE_ACTION: {"type": "complete_todo", '
                    '"payload": {"title": "Guitar"}, '
                    '"summary": "Complete todo: Guitar"}'
                ),
            ),
        ]
        with mock.patch.object(
            CocoService, "_resolve_payload",
            lambda self, uid, atype, parsed: {"todo_id": "t1", "title": "Guitar practice"},
        ):
            out, router = self._chat("Complete Guitar todo", results=results)
        self.assertGreaterEqual(router.calls, 1)
        self.assertIsNotNone(out.proposed_action)
        self.assertEqual(out.proposed_action.type, "complete_todo")

    # --- the headline guarantee ----------------------------------------------

    def test_all_non_ai_routes_have_zero_provider_calls(self):
        non_ai = [
            "hi", "hello", "thanks", "help", "what can you do",
            "what's the weather", "write my essay",
            "overall attendance", "can I skip DBMS", "safe skips",
            "assignments due this week", "overdue assignments",
            "today's todos", "all my todos", "is my timetable uploaded",
        ]
        for message in non_ai:
            with self.subTest(message=message):
                _, router = self._chat(message)
                self.assertEqual(router.calls, 0, f"{message!r} should cost 0 provider calls")

    # --- ephemeral-conversation cleanup ---------------------------------------

    def test_chat_prunes_conversations_older_than_24h(self):
        """Every chat first prunes messages older than the 24h retention window,
        with a cutoff of roughly now-24h (regardless of the route taken)."""
        service = CocoService(db=_FakeSession(), router=FakeRouter())
        before = datetime.now(timezone.utc)
        service.chat(user=self.user, payload=ChatIn(message="hi"))
        after = datetime.now(timezone.utc)

        cutoff = service.messages.pruned_before
        self.assertIsNotNone(cutoff, "cleanup should have run before serving")
        self.assertGreaterEqual(cutoff, before - timedelta(hours=24))
        self.assertLessEqual(cutoff, after - timedelta(hours=24))

    def test_cleanup_failure_never_blocks_the_request(self):
        """A raising cleanup is swallowed: the user still gets a normal reply."""
        service = CocoService(db=_FakeSession(), router=FakeRouter())
        with mock.patch.object(
            service.messages, "delete_older_than", side_effect=RuntimeError("db down")
        ):
            out = service.chat(user=self.user, payload=ChatIn(message="hi"))
        self.assertTrue(out.coco_available)
        self.assertTrue(out.reply)


if __name__ == "__main__":
    unittest.main()

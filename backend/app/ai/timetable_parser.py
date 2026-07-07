"""Timetable extraction via the vision router (Docs/03_System_Architecture.md §11).

The parser turns an uploaded PDF/image into structured subjects + slots. It only
extracts facts — the AI never guesses schedule data it cannot see, and the user
confirms/edits the result before anything is saved (Docs/05_Coco_Agent_Design.md).

STATUS: preserved for V2. V1 ships storage-only upload and does NOT call this
module (gated by `ENABLE_TIMETABLE_PARSING`). All prompts, validation, and
normalization here remain valid and reusable — only the provider call now goes
through the vision router (Phase 4.5) instead of talking to Gemini directly.

Failure is expected and handled: if the provider is unconfigured or errors, we
return an empty, FAILED result so the user can still build the timetable by hand
(Docs/03_System_Architecture.md §15). This module performs no persistence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from app.ai.interfaces.vision_provider import VisionRequest
from app.ai.routers.vision_router import get_vision_router

# JSON contract we ask Gemini to return. `day_of_week` is 1 (Mon)..7 (Sun);
# times are 24-hour "HH:MM" (Docs/04_Database_Design.md §6).
_PROMPT = """You are extracting a college class timetable from the attached file.

Return ONLY a JSON object (no markdown, no prose) with this exact shape:
{
  "subjects": [
    {
      "name": "string (subject/course name)",
      "faculty": "string or null",
      "classroom": "string or null",
      "slots": [
        {"day_of_week": 1-7 (1=Monday..7=Sunday),
         "start_time": "HH:MM" 24-hour,
         "end_time": "HH:MM" 24-hour,
         "room": "string or null"}
      ]
    }
  ],
  "confidence": 0.0-1.0
}

Rules:
- Group every lecture under its subject; one subject may have many slots.
- Use null for faculty/classroom/room you cannot read. Never invent them.
- Omit anything you cannot determine rather than guessing.
- If the file is not a timetable or is unreadable, return {"subjects": [], "confidence": 0.0}.
"""


@dataclass
class ParsedSlot:
    day_of_week: int
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    room: str | None = None


@dataclass
class ParsedSubject:
    name: str
    faculty: str | None = None
    classroom: str | None = None
    slots: list[ParsedSlot] = field(default_factory=list)


@dataclass
class ParseResult:
    subjects: list[ParsedSubject]
    confidence: Decimal
    succeeded: bool
    error: str | None = None

    @classmethod
    def failed(cls, error: str) -> "ParseResult":
        return cls(subjects=[], confidence=Decimal("0"), succeeded=False, error=error)


class TimetableParser:
    """Extracts timetable structure from an uploaded file via the vision router.

    The concrete vision provider (Gemini today, configurable via VISION_PROVIDER)
    is selected by the router; this parser stays provider-agnostic and owns only
    the prompt and the response validation/normalization.
    """

    def __init__(self, vision_router=None) -> None:
        # Injectable for testing; defaults to the configured vision router.
        self._router = vision_router or get_vision_router()

    @property
    def available(self) -> bool:
        return self._router.available

    def parse(self, *, content: bytes, mime_type: str) -> ParseResult:
        """Parse an upload into subjects + slots. Never raises: any failure is
        returned as a FAILED result so the caller can fall back to manual entry."""
        result = self._router.generate(
            VisionRequest(
                content=content,
                mime_type=mime_type,
                prompt=_PROMPT,
                json_response=True,
            )
        )
        if not result.ok:
            return ParseResult.failed(
                result.error or "Timetable parsing failed."
            )

        return self._parse_response(result.text)

    def _parse_response(self, raw: str) -> ParseResult:
        text = _strip_code_fence(raw).strip()
        if not text:
            return ParseResult.failed("AI returned an empty response.")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return ParseResult.failed(f"AI returned invalid JSON: {exc}")

        subjects: list[ParsedSubject] = []
        for raw_subject in data.get("subjects", []) or []:
            name = (raw_subject.get("name") or "").strip()
            if not name:
                continue
            slots: list[ParsedSlot] = []
            for raw_slot in raw_subject.get("slots", []) or []:
                slot = _coerce_slot(raw_slot)
                if slot is not None:
                    slots.append(slot)
            subjects.append(
                ParsedSubject(
                    name=name,
                    faculty=_clean_optional(raw_subject.get("faculty")),
                    classroom=_clean_optional(raw_subject.get("classroom")),
                    slots=slots,
                )
            )

        confidence = _coerce_confidence(data.get("confidence"))
        return ParseResult(subjects=subjects, confidence=confidence, succeeded=True)


def _strip_code_fence(text: str) -> str:
    """Remove a ```json ... ``` fence if the model added one despite instructions."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped[3:]
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    return stripped


def _clean_optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_slot(raw_slot: dict) -> ParsedSlot | None:
    """Validate a single slot; drop it if the essentials are missing/invalid."""
    try:
        day = int(raw_slot.get("day_of_week"))
    except (TypeError, ValueError):
        return None
    if not 1 <= day <= 7:
        return None

    start = _normalize_time(raw_slot.get("start_time"))
    end = _normalize_time(raw_slot.get("end_time"))
    if start is None or end is None:
        return None

    return ParsedSlot(
        day_of_week=day,
        start_time=start,
        end_time=end,
        room=_clean_optional(raw_slot.get("room")),
    )


def _normalize_time(value: object) -> str | None:
    """Accept "H:MM" / "HH:MM" (optionally with seconds) and return "HH:MM"."""
    if value is None:
        return None
    text = str(value).strip()
    parts = text.split(":")
    if len(parts) < 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return f"{hour:02d}:{minute:02d}"


def _coerce_confidence(value: object) -> Decimal:
    try:
        conf = Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError):
        return Decimal("0")
    if conf < 0:
        return Decimal("0")
    if conf > 1:
        return Decimal("1")
    return conf

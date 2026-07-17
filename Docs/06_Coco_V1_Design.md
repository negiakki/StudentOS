# StudentOS — Coco V1 Design (Phase 9)

**Version:** 1.0
**Status:** Proposed — for review before implementation
**Supersedes:** refines `05_Coco_Agent_Design.md` for what is *actually built* as of Phase 8

---

# Part 1 — Assessment of the Current System

## 1.1 What exists today

| Module | Backend surface | Data Coco can use |
|---|---|---|
| **Auth / Users** | `GET /users/me`, onboarding | name, college, degree, onboarding state |
| **Timetable** | `POST/GET/DELETE /timetable` — **storage-only** | the uploaded file reference only. **No subjects/days/timings** (parsing deferred to V2, `ENABLE_TIMETABLE_PARSING=false`) |
| **Attendance** | `/attendance/overview`, subjects CRUD, per-day records | per-subject attended/total, **percentage, safe skips, threshold warnings** (all computed in `AttendanceService`), calendar records, history |
| **Assignments** | `/assignments` CRUD + `/assignments/dashboard` | title, description, subject link, due date, priority, status; **Overdue / Due Today / Upcoming grouping** (computed in `AssignmentService`) |
| **Todo** | `/todos` CRUD | title, due date, priority, completed; **"today's tasks"** (computed in `TodoService`) |
| **Dashboard** | frontend-composed from the endpoints above | no backend aggregate endpoint yet |

## 1.2 Existing infrastructure Coco must reuse

* **AI provider layer (Phase 4.5)** — `app/ai/`: `ChatProvider` interface → `ChatRouter` (selected by `CHAT_PROVIDER`) → `OpenRouterChatProvider` (**currently a stub**; completing it is part of this phase). The app only ever talks to the router. `ChatRequest` = messages + temperature; `ChatResult` = `ok / text / error` (graceful failure, never raises).
* **Layering** — API route → Service → Repository → DB; every query scoped to the JWT user via `CurrentUserDep`. Coco slots into this identically.
* **`chat_messages` table (Phase 3)** — already migrated: `user_id`, `conversation_id`, `role (USER | COCO)`, `message`, `created_at`. No new migration is required.
* **Frontend conventions** — `services/*.ts` on top of `apiFetch`, feature folders under `features/*`, protected routes.

## 1.3 Reality check vs. the original Coco doc (05)

The original design assumed capabilities V1 doesn't have. Coco V1 must be honest about them:

| Original tool | V1 status |
|---|---|
| Timetable Tool (today's classes, next class) | ❌ **Not possible** — no structured schedule data. Coco can only report whether a timetable file is uploaded and direct the user to view it. Subject *names* exist (from attendance setup), so "what subjects do I have" works — via attendance, not timetable. |
| Weather Tool | ❌ No weather service exists. V2. |
| Notification Tool | ❌ No notification service exists. V2. |
| Dashboard Tool / Daily Brief | ⚠️ No backend aggregate exists; V1 adds a *daily snapshot* composition (see §4) which also unlocks the PRD's Daily Brief as a nice-to-have. |
| Attendance / Assignment / Todo tools | ✅ Fully backed by existing services. |
| Gemini as primary chat | Changed in Phase 4.5: **OpenRouter is primary chat**, Gemini is vision. Config-only decision; unchanged here. |

## 1.4 Key technical constraint discovered

The `ChatProvider` interface is **plain text-in/text-out** — it has no native function-calling. Rather than extend every provider with provider-specific tool-call APIs, Coco V1 uses a **prompted two-call flow** (select tool as strict JSON → run tool in Python → explain result). This keeps the provider interface untouched, works with any model on OpenRouter, and keeps Coco deterministic. See §8.

---

# Part 2 — Coco V1 Design

## 2. Identity

**Who:** Coco is the student's academic co-pilot inside StudentOS — the interface that *interprets* their data instead of making them read it. Coco is not a general-purpose chatbot and not the AI model itself; Coco is StudentOS's intelligence layer. The model generates language; StudentOS provides every fact.

**Personality (per PRD §13):**

* Friendly, encouraging, never robotic — a helpful senior, not a lecturing professor.
* **Concise first** — answers in 1–3 sentences, then detail only if useful. Mobile-first chat panel; no walls of text.
* **Grounded** — every number (percentage, safe skips, due dates) comes from a tool result. Coco never estimates, never pads, never invents. If the data doesn't exist, Coco says so plainly.
* **Honest about limits** — "I can't read your timetable's class timings yet — that's coming in V2. You can view the uploaded file on the Timetable page."
* Light emoji use is fine (matches the dashboard's "Good Morning, Akshat 👋"), never more than one per message.

**Voice examples:**

> "You're at 71.4% in DBMS — below your 75% target. You'd need to attend the next 4 classes straight to get back over."
>
> "Two things due tomorrow: the OS lab report (High priority) and the Maths problem set. Want me to add a todo to start tonight?"
>
> "I don't have your class timings yet — timetable parsing lands in V2. I *can* tell you your attendance and what's due."

## 3. Capabilities

Everything below is fully backed by an existing service. Nothing else ships in V1.

**Answering & interpreting (read):**

1. Attendance status — overall and per subject: percentage, attended/total, threshold warnings.
2. **Safe-skip questions** — "Can I skip DBMS?" → safe_skips from `AttendanceService` (the flagship interaction).
3. Attendance history — "Was I present in DBMS last Friday?", recent records, unmarked-day nudges ("You haven't marked anything today").
4. Assignment questions — what's due today / tomorrow / this week, what's overdue, priorities, per-subject filtering.
5. Todo questions — today's tasks, open tasks, what's overdue.
6. Subject list — from attendance setup ("What subjects am I tracking?").
7. **Summarize my day** — one composed snapshot: attendance warnings + due/overdue assignments + today's todos (the daily-snapshot read, §4).
8. Prioritization *within the data* — "What should I do first?" → Coco orders the snapshot by overdue > due today > priority. This is language over tool data, not a new calculation.
9. Light study suggestions *derived from the data* — "What should I study tonight?" → based on due assignments and below-threshold subjects. No invented syllabus content.
10. Profile/app questions — "What can you do?", onboarding state, whether a timetable file is uploaded.

**Doing (write, via confirmation — §4):**

11. Create a todo ("remind me to submit the lab record Friday").
12. Create an assignment ("I got a DBMS assignment due next Monday, high priority").
13. Complete a todo ("done with the maths revision").
14. Mark attendance for today ("I attended all classes today" / "mark me present in DBMS").

**Explicitly out (V1):** class timings / next class / "where is my class" (no parsed timetable), weather, notifications, multi-day study plans, anything requiring memory across conversations, general-knowledge tutoring (Coco may answer one-liners but redirects to its purpose).

## 4. Actions

### Read actions (Coco executes immediately)

Thin, read-only adapters over existing services — **no new business logic**:

| Tool | Backed by | Returns (compact JSON) |
|---|---|---|
| `get_attendance_overview` | `AttendanceService.overview` | overall %, threshold, per-subject {name, attended, total, pct, safe_skips, meets_threshold} |
| `get_subject_attendance` | `AttendanceService.get_subject` (+ fuzzy name→id resolution in the Coco layer) | one subject's figures |
| `get_attendance_records` | `AttendanceService.list_records` | recent records for a subject (date, status) |
| `get_assignments` | `AssignmentService.dashboard` / `list` | overdue / due-today / upcoming (capped, see §5) |
| `get_todos` | `TodoService.today` / `list` | open todos (capped) |
| `get_daily_snapshot` | composition of the three services above (server-side, one tool) | attendance warnings + assignment groups + today's todos + profile name |
| `get_timetable_status` | `TimetableService.get_file` | has_file + filename only (never the file content) |

`get_daily_snapshot` exists so "summarize my day" is **one tool call, not an agent loop** — the composition happens in Python, honoring the no-agents constraint. It also becomes the input for the PRD's Daily Brief (nice-to-have).

### Write actions (Coco proposes; the user confirms; existing endpoints execute)

V1 writes use a **propose → confirm** pattern:

1. Coco parses the intent and returns a structured `proposed_action` alongside its reply — e.g. `{type: "create_todo", payload: {title: "Submit lab record", due_date: "2026-07-18", priority: "MEDIUM"}}`.
2. The frontend renders it as a **confirmation card** (title, fields, Confirm / Cancel).
3. On Confirm, the frontend calls the **existing REST endpoint** (`POST /todos`, `POST /assignments`, `PATCH /todos/{id}`, `PUT /attendance/subjects/{id}/records/{date}`) through the existing `services/*.ts` — exactly as if the user had used the form.

| Write action | Executes via |
|---|---|
| `create_todo` | `POST /todos` |
| `create_assignment` | `POST /assignments` |
| `complete_todo` | `PATCH /todos/{id}` (Coco resolves which todo by title match; ambiguity → follow-up question) |
| `mark_attendance` | `PUT /attendance/subjects/{id}/records/{date}` (per subject, PRESENT/ABSENT) |

Why this shape:

* **No server-side action state, no second Coco round-trip** — stateless, simple, no agent loop.
* **All validation, ownership checks, and delta math stay in the existing services** — zero duplicated logic, zero new write paths to secure.
* **The user always sees exactly what will happen before it happens** — the model can never mutate data on a misparse.
* The dashboard/pages refresh through the same client code paths that already work.

**No deletes via Coco in V1.** Destructive actions stay in the UI where the object is visible. (V2 can add delete with the same confirm pattern.)

## 5. Context

### What Coco receives per message

1. **System prompt** (static, cached): identity, tone rules, grounding rules ("never state a number that isn't in TOOL_RESULT"), refusal rules, output format.
2. **Per-request line:** today's date (server-side, ISO) + the user's first name. Date goes in explicitly so "tomorrow"/"next Monday" resolve deterministically.
3. **Short conversation window:** the last **6 messages** (3 turns) of the current conversation, loaded from `chat_messages` by `conversation_id`. This is *conversation context*, not memory — nothing persists across conversations, no facts are extracted or stored, honoring the no-memory constraint.
4. **The selected tool's result only** — compact JSON, injected into the second model call.

### How context is constructed (two-call flow)

* **Call 1 (tool selection):** system prompt = the tool catalog only — name, one-line description, args schema per tool (~400 tokens total) + conversation window + user message. Output: strict JSON `{tool, args}` / `{action, payload}` / `{tool: null}`. Low temperature (0.1).
* **Call 2 (answering):** identity prompt + user message + `TOOL_RESULT` JSON. The tool catalog is **not** sent again. Normal temperature (0.7).

### Token minimization rules

* **Never dump all data** — only the one selected tool's result. A safe-skip question never carries assignment data.
* **Caps computed in Python**: assignments capped at 10 per group, todos at 15, attendance records at 30 (existing service default) — with a `truncated: true` flag so Coco can say "…and N more".
* **Compact JSON**: short keys, no nulls, dates as `YYYY-MM-DD`, no ORM noise (no UUIDs in call 2 except where an action needs one).
* **History window is 6 messages, text-only** — old tool results are *not* replayed into context.
* **Timetable file content is never sent** to the chat model (it's an image/PDF; chat is text).
* System prompts are static strings → provider-side prompt caching benefits when available.

Typical request: ~600–900 tokens in, ~150 out for call 1; ~700–1,200 in, ~200 out for call 2. Well inside free-tier friendly territory.

## 6. Safety

### Coco refuses (politely, with a pointer) when:

* Asked to state data it doesn't have — timings, grades, exam dates, syllabus content, weather. *"I don't have that — here's what I can see: …"* Never guess. This is the #1 rule.
* Asked to delete anything, modify another user's data, or bulk-modify ("clear all my attendance"). → point to the relevant page.
* Asked for medical/mental-health advice — brief empathy, suggest talking to someone qualified; no counseling.
* Asked to do open-ended general-knowledge work (write my essay, solve this assignment) — one-line redirect: Coco manages the work, it doesn't do the coursework.
* The request needs capabilities that are V2 ("when is my next class?") — say so honestly and name the workaround.

### Coco asks a follow-up question (instead of guessing) when:

* **Subject is ambiguous** — "mark me present" with 5 subjects → "For which subject — or all of today's?" Fuzzy name matching resolves obvious cases ("dbms" → "DBMS"); anything below a confident match asks.
* **A required field is missing for a write** — assignment with no title; "remind me to study" with no discernible task.
* **A date is ambiguous** — "next week sometime" → propose a concrete date in the confirmation card (user can still cancel), but ask when even a proposal would be a coin flip.
* **A todo/assignment reference matches multiple items** — "mark the lab one done" with two lab todos.

One follow-up maximum per exchange; if still unclear, point to the form UI.

### Structural safety (independent of the model):

* Every tool runs through existing user-scoped services — the model physically cannot reach other users' data; IDs come from the JWT, never from model output.
* Writes require an explicit user tap on a confirmation card.
* Tool args from call 1 are **validated with Pydantic** before any service call; invalid args → re-ask, never execute.
* Provider failure → the CLAUDE.md-mandated fallback: *"Coco is temporarily unavailable. Your StudentOS data is still available."* Every other module keeps working (Architecture §15).

## 7. V1 Scope

### Must Have

1. `OpenRouterChatProvider.complete()` implemented (fills the Phase 4.5 stub; httpx, graceful `ChatResult.failure`).
2. `POST /coco/chat` endpoint + `CocoService` orchestrator (two-call flow).
3. Read tools: `get_attendance_overview`, `get_subject_attendance`, `get_assignments`, `get_todos`, `get_daily_snapshot`, `get_timetable_status`.
4. Write proposals with confirmation cards: `create_todo`, `complete_todo`, `create_assignment`.
5. Chat persistence to the existing `chat_messages` table; 6-message context window.
6. Frontend: Coco side panel (per CLAUDE.md checklist) — opens from any protected page, message list, input, confirmation cards, loading state, unavailable-fallback state.
7. Safety behaviors of §6 (validation, refusal prompts, follow-up rule).

### Nice to Have (in-phase if time allows)

1. `mark_attendance` write action (highest-friction daily task; slightly harder — needs subject + status resolution).
2. `get_attendance_records` read tool ("was I present last Friday?").
3. **Daily Brief on the dashboard** — one templated model call over `get_daily_snapshot`, no tool selection needed; fills the PRD §6 slot.
4. Suggested prompt chips in the empty chat state ("Can I skip a class?", "What's due this week?", "Summarize my day").
5. Conversation history loaded when the panel reopens (same `conversation_id` per day/session).

### V2 (explicitly deferred)

* Timetable Q&A (needs `ENABLE_TIMETABLE_PARSING=true` + parsed slots) — next class, today's classes, "where is my class".
* Weather tool, Notification tool, attendance/assignment reminders.
* Deletes and bulk edits via Coco.
* Multi-step study plans, cross-conversation memory, personalization.
* Streaming responses; multi-tool composition beyond the built-in snapshot; voice/avatar (PRD out-of-scope list).

## 8. Architecture

### Request flow (unchanged philosophy from doc 05, adapted to reality)

```text
User message (side panel)
        ↓
POST /coco/chat            ── existing auth (CurrentUserDep), existing apiFetch
        ↓
CocoService
        ↓
[Call 1] ChatRouter.complete(tool-selection prompt)   → {tool, args} JSON
        ↓
Validate args (Pydantic) → run ONE tool → existing Service → Repository → DB
        ↓
[Call 2] ChatRouter.complete(answer prompt + TOOL_RESULT)
        ↓
{ reply, proposed_action? }  → persisted to chat_messages
        ↓
Frontend renders reply (+ confirmation card if proposed_action)
        ↓ (on Confirm)
Existing REST endpoint via existing services/*.ts     ── Coco not involved
```

### New components (and only these)

**Backend**

```text
app/api/coco.py            POST /coco/chat  (+ GET /coco/history?conversation_id=…)
app/services/coco_service.py    orchestrator: prompts, 2-call flow, persistence
app/services/coco_tools.py      tool registry: name → {description, args schema,
                                 handler}. Handlers are 3–5 line adapters that call
                                 existing services and compact their output.
app/schemas/coco.py             ChatIn / ChatOut / ProposedAction / tool-arg models
```

**Frontend**

```text
features/coco/CocoPanel.tsx       side panel: messages, input, states
features/coco/ConfirmActionCard.tsx  renders proposed_action → calls existing service fns
services/coco.ts                  sendMessage(), getHistory()
types/coco.ts
```

### API contract (design-level)

```jsonc
// POST /coco/chat
// → { "message": "Can I skip DBMS tomorrow?", "conversation_id": "…" | null }
// ←
{
  "conversation_id": "…",
  "reply": "Yes — you're at 82% in DBMS with 3 safe skips left.",
  "proposed_action": null,          // or:
  // { "type": "create_todo",
  //   "payload": { "title": "…", "due_date": "2026-07-18", "priority": "MEDIUM" },
  //   "summary": "Add todo “Submit lab record”, due Fri 18 Jul" }
  "coco_available": true            // false → frontend shows the fallback line
}
```

### What is deliberately NOT introduced

* **No agent loop** — exactly one tool call per message, chosen once, executed deterministically in Python. "Summarize my day" stays one call because composition lives in `get_daily_snapshot`.
* **No memory** — only the last-6-message window of the current conversation; no fact extraction, no cross-session state.
* **No new write paths** — writes reuse the Phase 7/8 endpoints verbatim, triggered by the frontend after user confirmation.
* **No provider-specific function-calling** — the `ChatProvider` interface stays as-is; tool selection is prompted JSON, so swapping OpenRouter models (or adding a Gemini chat provider later) remains a config change.
* **No new tables, no migration** — `chat_messages` already exists.
* **No changes to existing modules** — every existing service is consumed read-only through its current public methods.

### Failure handling

| Failure | Behavior |
|---|---|
| Provider unavailable / call 1 fails | `coco_available: false` + fallback line; rest of app unaffected |
| Call 1 returns malformed JSON | one retry with a stricter instruction; then answer without a tool ("I couldn't work that out — try rephrasing?") |
| Tool args invalid | never execute; Coco asks the follow-up |
| Tool/service raises | Coco reports that feature is having trouble; other tools unaffected |
| Call 2 fails after a successful tool run | fallback line (data was read-only; nothing to roll back) |

---

# 9. Decisions taken (flag if you disagree)

1. **Prompted-JSON tool selection over native function-calling** — keeps the Phase 4.5 provider interface untouched and provider-agnostic. Revisit in V2 if models misroute in practice.
2. **Writes execute through the frontend after confirmation**, not through the backend Coco path — the strongest safety property for the least machinery. If we later want "Coco executes after confirm," the confirm card can call a `/coco/execute` endpoint without changing this design's contracts.
3. **`get_daily_snapshot` as a composed read tool** — the sanctioned way to answer multi-module questions without multi-tool loops.
4. **Conversation window = 6 messages, per-conversation, no cross-session memory** — reads as "chat that remembers what you just said," not "assistant that remembers you," per the constraints.
5. **Timetable honesty** — Coco explicitly names the V2 boundary instead of deflecting vaguely.

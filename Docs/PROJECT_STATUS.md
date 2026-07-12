# PROJECT_STATUS.md

**Project:** StudentOS

**Current Version:** v1.0

**Status:** Development

---

# Project Goal

Build an AI-powered student dashboard with Coco as an intelligent assistant.

Target users:

* College students

Primary MVP:

* Timetable upload
* Dashboard
* Attendance
* Assignments
* Todo
* Coco

---

# Current Phase

🟢 Phase 9 — Coco

Status: ⬜ Not Started (next up)

Phase 8 (Todo) is complete. It added full CRUD for todos (title, optional due
date, completion toggle), a dashboard `TodoCard`, and a new Quick Actions tile
linking to `/todo`. Alongside it, a reusable `DatePicker` component was built
as a UX enhancement and adopted by both Assignments and Todo, with no
backend/API contract changes.

(Phase 1 ✅ · Phase 2 ✅ · Phase 3 ✅ · Phase 4 — Timetable Upload (Storage Only):
✅ Complete — upload → Supabase Storage → save reference → display. Instant, no
AI. Phase 4.5 — AI Provider Layer: ✅ Complete — interfaces → providers → routers;
app talks only to routers; provider choice is config. Automatic parsing is
postponed to V2 and preserved behind `ENABLE_TIMETABLE_PARSING=false`. Backend +
frontend build/lint clean; live upload/replace/delete verified against real
Supabase Storage + DB with no AI called.)

## V1 Simplification (product decision)

Automatic timetable parsing (OCR/AI) is postponed to V2 to ship a polished V1
fast. V1 upload is storage-only. All parser code — prompts, validation,
normalization, schemas — is preserved and reachable in V2 by flipping
`ENABLE_TIMETABLE_PARSING=true` (deferred to V2; see "Deferred to V2" below).

---

# Development Roadmap

## Phase 1

Repository Setup

Status

✅ Complete (remote GitHub repo pending owner action)

Tasks

* ✅ Create GitHub Repository — pushed to github.com/negiakki/StudentOS (`main`)
* ✅ Create Frontend — Next.js 15 (App Router) + TS + Tailwind, builds clean
* ✅ Create Backend — FastAPI app boots, `/health` verified
* ✅ Configure Folder Structure — per System Architecture §4
* ✅ Add Documentation — root + backend + frontend READMEs
* ✅ Initial Commit — local git repo on `main`

---

## Phase 2

Authentication

Status

✅ Complete (2 owner dashboard steps pending — see notes)

Tasks

* ✅ Configure Supabase — @supabase/ssr browser/server/middleware clients (latest API)
* ✅ Google Authentication — signInWithOAuth (PKCE code flow via /auth/callback)
* ✅ Email & Password Authentication — signInWithPassword + signUp
* ✅ Email Verification — /auth/callback (code) + /auth/confirm (token_hash) routes
* ✅ Forgot Password — resetPasswordForEmail + /reset-password (updateUser)
* ✅ Protected Routes — root middleware + guarded (protected) layout
* ✅ Persistent Sessions — cookie-based token refresh in middleware
* ✅ Backend JWT validation — Supabase ES256 via JWKS (+ HS256 fallback), get_current_user, /auth/me

Owner dashboard steps still required to exercise live:
* Enable + configure the **Google** provider in Supabase (client id/secret).
* Add redirect URLs to Supabase Auth allowlist: `http://localhost:3000/auth/callback`
  (and the production origin when deployed).

---

## Phase 3

Database

Status

✅ Complete — migration applied to Supabase and verified live

Tasks

* ✅ SQLAlchemy Models — all 11 tables + enums (SQLAlchemy 2.0 typed models)
* ✅ Alembic Migrations — env wired to settings/metadata; initial migration generated + upgrade/downgrade verified
* ✅ Repository Layer — BaseRepository + UserScopedRepository + User/Settings repos
* ✅ Service Layer — UserService (get-or-create profile, onboarding) via repos
* ✅ Database Connection — engine + session + get_db dependency

Verified: 11 tables build; relationships + cascade account-delete; full
api→service→repository→db flow for /users/me (idempotent) and onboarding; auth enforced.

Live: migration applied to Supabase (PostgreSQL 17.6) via `alembic upgrade head`;
all 11 tables + alembic_version present; `alembic check` reports zero drift; a
live /users/me + onboarding round-trip (with cascade cleanup) passed against Supabase.

---

## Phase 4

Timetable Upload (Storage Only)

Status

✅ Complete — upload → Supabase Storage → save reference → display, verified live

V1 flow (no AI, instant): upload a PDF/PNG/JPG → store it → save the file
reference → show the uploaded file. Replace and delete supported. Automatic
parsing (subjects/days/timings extraction) is deferred to V2 (see below).

Tasks

* ✅ File Upload — `POST /timetable/upload` (multipart); PDF/PNG/JPG only, 10 MB
  cap, empty/oversized/unsupported rejected with clear errors
* ✅ Storage — `StorageService` writes to Supabase Storage (service-role key, REST
  via httpx); files namespaced per user (`{user_id}/timetable/…`), re-upload
  upserts and orphaned objects (on type change) are cleaned up; signed view URLs
* ✅ Save reference — one `uploaded_files` row per user (upsert); stores user_id,
  storage_path, uploaded_at, filename, mime_type; `parsing_status = PENDING`
  (parser fields kept, unused in V1)
* ✅ Display / Replace / Delete — `GET /timetable` returns the file + signed URL;
  frontend shows the image inline (or PDF in an iframe); `DELETE /timetable`
  removes storage object + row

Preserved for V2 (gated by `ENABLE_TIMETABLE_PARSING=false`, HTTP 404 while off):
`POST /timetable/parse`, `POST /timetable/confirm`, `GET /timetable/subjects`,
backed by the preserved parser, preview/save schemas, and service methods.

Architecture: routes → `TimetableService` → repositories → DB, plus
`StorageService`; auth-scoped to the JWT user (no user id from the client).
Frontend: authed `apiFetch` (FormData-aware), `services/timetable.ts`,
`types/timetable.ts`, `features/timetable/TimetableUpload.tsx`, protected
`/timetable` page.

Verified: backend imports + OpenAPI generate; frontend `next build` + `next lint`
clean (`/timetable` route present). Live against real Supabase: storage-only
upload, get (with signed URL), replace (PNG→PDF with orphan cleanup), single-row
invariant, and delete — with **no AI provider called**; the gated V2 path refuses
while parsing is disabled.

---

## Phase 4.5

AI Provider Layer

Status

✅ Complete — interfaces → providers → routers; provider choice is config

The application talks only to the vision/chat routers; it never imports a
provider directly. Switching providers requires editing only `.env`
(Docs/03_System_Architecture.md §13).

Tasks

* ✅ Interfaces — `app/ai/interfaces/vision_provider.py`, `chat_provider.py`
  (ports every provider implements)
* ✅ Providers — `app/ai/providers/gemini.py` (VisionProvider, primary),
  `app/ai/providers/openrouter.py` (ChatProvider stub for Phase 6, fails
  gracefully)
* ✅ Routers — `app/ai/routers/vision_router.py`, `chat_router.py` select the
  provider by `VISION_PROVIDER` / `CHAT_PROVIDER`, with safe fallback
* ✅ Parser rewired — `timetable_parser.py` now calls the vision router (prompts,
  validation, normalization unchanged), so V2 parsing works through the layer
* ✅ Config — `VISION_PROVIDER`, `CHAT_PROVIDER`, `OPENROUTER_API_KEY`,
  `OPENROUTER_MODEL`, `ENABLE_TIMETABLE_PARSING` added to settings + `.env(.example)`

Phase 6 (Coco): use OpenRouter as primary chat, Gemini as primary vision, both
through the routers.

Verified: routers resolve providers; Gemini vision reports available; OpenRouter
chat stub reports unavailable and fails gracefully; parser produces correct
structured output via an injected fake router.

---

## Phase 5

Dashboard

Status

✅ Complete — reviewed, manually tested, and pushed

Product decisions (V1):
* No "Today's Classes" — timetable parsing is disabled, so there is no
  structured schedule data. Replaced by a "My Timetable" card that displays the
  uploaded file directly. Designed as a self-contained component so V2 can swap
  it for Today's Classes without wider refactoring.
* Attendance is fully manual — the user creates semester subjects (name, classes
  attended, total). No subject detection from the timetable (postponed to V2).

Tasks

* ✅ Greeting — time-of-day + name (client-computed to avoid hydration mismatch)
* ✅ Attendance Overview — overall % + per-subject bars, safe-skips, below-target
  warnings; empty state links to setup. All figures computed in Python.
* ✅ My Timetable — inline image/PDF preview of the uploaded file (view-only;
  replace from the timetable page)
* ✅ Quick Actions — navigation hub (Timetable, Attendance)
* ✅ Recent Tasks — calm placeholder (to-dos land in a later phase)
* ✅ Manual attendance backend — subjects + attendance_summary CRUD; percentage
  and safe-skip calculations; `/attendance` API + setup page
* Deferred to later phases: Weather, Assignments, Todo, Daily Brief

Verified: backend imports + routes; attendance calculations and full
service→repository→DB flow (create/list/overview/update/delete, ownership
scoping, attended≤total invariant) on SQLite; frontend typecheck + lint + prod
build clean. In-browser click-through completed during review.

Polish pass (post-review): light-mode form input text/placeholder legibility,
"← Dashboard" back-navigation on the Attendance and Timetable pages, and
System (default) / Light / Dark theme support — persisted to localStorage,
applied pre-paint to avoid a flash, with a small toggle beside Sign out. No
feature, architecture, AI-layer, or parser changes; typecheck + lint + build clean.

Not built (stay in later phases): daily attendance marking, calendar,
edit-previous-days, safe-skip on the attendance page beyond the computed figure.

---

## Phase 6

Attendance

Status

✅ Complete — reviewed, approved, and pushed

Product decision (V1): the Phase 5 attendance setup (attended/total per subject)
is treated as a **baseline**; each daily mark applies a **delta** to the stored
summary (present → +1 attended / +1 total; absent → +1 total; edit → ±1 attended;
clear → reverse). This keeps percentage / safe-skips always derived, needs no
schema change (the `attendance_records` table already exists from Phase 3), and
makes records the single source for both the Calendar and the Attendance History.
"Today" labels are computed on the frontend (timezone-safe); the backend is
date-agnostic and stores only the ISO day it is sent.

Tasks

* ✅ Attendance Setup — carried over from Phase 5 (subjects + baseline counts)
* ✅ Mark Present / Mark Absent — `PUT /attendance/subjects/{id}/records/{date}`
  (upsert); today's status has one-tap Present / Absent / Clear on the subject page
* ✅ Edit Previous Days — the same upsert endpoint on any past date, driven from
  the month calendar (pick a day → Present / Absent / Clear)
* ✅ Calendar View — `GET …/records?start&end`; month grid with present/absent
  colouring, future days disabled, month navigation capped at the current month
* ✅ Attendance History — recent records list on the subject page
  (`GET …/records?limit`), same data as the calendar
* ✅ Safe Skip Calculation — surfaced on the subject page (computed in Python,
  unchanged from Phase 5)
* ✅ Clear a day — `DELETE …/records/{date}` (reverses the delta; idempotent)

Architecture: routes → `AttendanceService` (delta math, all calculations) →
`AttendanceRecordRepository` / `AttendanceSummaryRepository` → DB; every query is
scoped to the authenticated user through the parent subject. Frontend: subject
detail page `/attendance/[id]` with `SubjectDetail` + `AttendanceCalendar`, new
service methods, and `lib/date.ts` local-date helpers.

Verified (targeted): backend imports + routes; a SQLite service e2e (baseline +
mark/edit/clear deltas, history desc, calendar range asc, ownership scoping,
attended≤total invariant) and a FastAPI TestClient smoke (status codes, enum
validation 422, 404 scoping, nested response serialization); frontend typecheck +
lint + prod build clean (`/attendance/[id]` route present). No AI-layer, parser,
or migration changes. In-browser click-through completed during review.

---

## Phase 7

Assignments

Status

✅ Complete — verified, ready to merge

Assignments carry a title, optional description, optional subject link,
optional due date, and priority (Low/Medium/High); status is binary
(Pending/Completed). The dashboard groups pending assignments into Overdue,
Due Today, and Upcoming — undated assignments are treated as Upcoming (nothing
to be overdue against) — with all grouping and sorting (soonest due date
first, undated last) computed in Python per-request, never persisted. The
`assignments` table and its enums already existed from the Phase 3 schema, so
this phase added the API/service/repository/schema layers and the frontend on
top of it — no new migration was needed.

Tasks

* ✅ Create — `POST /assignments`, always starts Pending
* ✅ Edit — `PATCH /assignments/{id}`, partial update; subject_id ownership
  validated (400 if not owned/doesn't exist); nullable fields (description,
  subject_id, due_date) can be explicitly cleared
* ✅ Delete — `DELETE /assignments/{id}`, idempotent
* ✅ Dashboard Integration — `GET /assignments/dashboard` (Overdue/Due
  Today/Upcoming); `AssignmentsCard` on the dashboard replaces the Phase 5
  "Recent Tasks" placeholder; new Quick Actions tile links to `/assignments`

Architecture: routes → `AssignmentService` (subject-ownership checks, sorting,
dashboard grouping) → `AssignmentRepository` (plain `UserScopedRepository`,
no custom queries) → DB; every query scoped to the authenticated user.
Frontend: `/assignments` page with `AssignmentsManager` (add form, Pending/
Completed sections, inline edit, complete/reopen toggle, delete,
client-side overdue highlighting), `services/assignments.ts`,
`types/assignment.ts`.

Verified: backend imports clean (`/assignments` routes present); frontend
typecheck + lint + prod build clean (`/assignments` route present). No
migration, AI-layer, or parser changes.

---

## Phase 8

Todo

Status

✅ Complete — implementation review, pre-merge review, manual testing, and
repository integrity verification all passed

Backend

* ✅ Todo repository — plain `UserScopedRepository`, no custom queries
* ✅ Todo service — create/list/complete/delete logic, every query scoped to
  the authenticated user
* ✅ Todo schemas — request/response models for the API layer
* ✅ Todo API — `POST/GET/PATCH/DELETE /todos`
* ✅ Router registration — Todo routes wired into `main.py`

Frontend

* ✅ Todo page — protected `/todo` route
* ✅ TodoManager — add/complete/delete UI, using the shared `DatePicker` for
  due dates
* ✅ Dashboard TodoCard — surfaces todos on the dashboard
* ✅ Quick Actions integration — new tile linking to `/todo`
* ✅ API service — `services/todo.ts`
* ✅ Types — `types/todo.ts`

Verification

* ✅ CRUD verified — create, complete, delete exercised end-to-end
* ✅ Dashboard integration verified — `TodoCard` renders live data
* ✅ TypeScript — typecheck clean
* ✅ Production build — `next build` clean
* ✅ Manual testing — click-through completed during review

---

## Phase 9

Coco

Status

🟢 Current Phase — Not Started

Tasks

* Tool Layer
* Dashboard Tool
* Attendance Tool
* Timetable Tool
* Assignment Tool
* Todo Tool
* Weather Tool
* AI Integration

---

## Phase 10

Testing & Deployment

Status

⬜ Not Started

Tasks

* End-to-End Testing
* Bug Fixes
* Deploy Backend
* Deploy Frontend
* Production Verification

---

# Deferred to V2

* **Automatic Timetable Parsing** — extract subjects/days/timings from the
  uploaded file via the vision router (Gemini). Code is complete and preserved
  (`app/ai/timetable_parser.py`, preview/save schemas, `TimetableService`
  parse/confirm methods, `/timetable/parse|confirm|subjects` routes). Enable by
  setting `ENABLE_TIMETABLE_PARSING=true`, then rebuild the frontend
  preview/confirm UI (removed from V1; recoverable from git —
  `frontend/features/timetable/TimetableManager.tsx`).
* **Coco chat (OpenRouter)** — provider is a stub; complete in Phase 6.

---

# Known Constraints

* Current semester only
* Mobile-first design
* Free-tier infrastructure
* Single uploaded timetable per user
* No ERP integration
* No native mobile app

---

# Engineering Rules

* Follow the PRD.
* Follow the System Architecture.
* Follow the Database Design.
* Coco never accesses the database directly.
* Python performs all calculations.
* AI explains results.
* Build one phase at a time.
* Do not add features outside the MVP without approval.

---

# Completion Criteria

StudentOS v1 is complete when a user can:

* Create an account (Google or Email)
* Complete onboarding
* Upload a timetable
* Confirm parsed classes
* Enter initial attendance
* View their dashboard
* Manage attendance
* Manage assignments
* Manage todos
* Interact with Coco
* Use the application on desktop and mobile

---

## Claude Working Rules

Unless explicitly instructed otherwise:

- Work only on the current phase.
- Read only files required for the task.
- Do not revisit previous architecture.
- Do not implement future phases.
- Use targeted verification only.
- Keep commits focused.
- Do not push automatically.
- Keep responses concise.

---

# Change Log

Version 1.0

* Initial project planning completed.
* Architecture frozen.
* Development ready.
* Phase 1 (Repository Setup) implemented: backend + frontend scaffolds, folder
  structure per architecture, docs, local git repo + initial commit. Pushed to
  github.com/negiakki/StudentOS.
* Phase 2 (Authentication) implemented: Supabase Auth via current @supabase/ssr
  APIs (browser/server/middleware clients, PKCE), email/password + Google OAuth,
  email verification, forgot/reset password, cookie-based persistent sessions,
  middleware-protected routes. Backend verifies Supabase ES256 JWTs via JWKS
  (HS256 fallback) with get_current_user + /auth/me. Verified at runtime:
  protected routes redirect unauthenticated users; backend rejects invalid tokens.
* Phase 3 (Database) implemented: SQLAlchemy 2.0 models for all 11 tables + enums,
  UUID PKs, indexes, cascade relationships; Alembic env + initial migration
  (upgrade/downgrade verified); DB session layer (get_db); repository layer
  (base + user-scoped + User/Settings) and service layer (UserService); /users/me
  and onboarding endpoints exercising the full stack. Verified offline on SQLite.
  Pending: apply migration to Supabase once DATABASE_URL is set.
* Phase 4 (Timetable Upload) implemented: `POST /timetable/upload` stores the file
  in Supabase Storage (per-user path, upsert) and parses it with Gemini Vision into
  a structured, editable preview; `POST /timetable` saves the user-confirmed
  subjects + slots (one timetable per user, replacing any prior one); `GET
  /timetable` reads it back. New `StorageService`, AI `timetable_parser` (graceful
  fallback to manual entry when the AI is unavailable), timetable repositories,
  `TimetableService`, and schemas. Frontend: protected `/timetable` page with
  upload + full manual editor (`features/timetable/TimetableManager`), authed API
  helper, service, and types. Backend + frontend build clean; live round-trips
  verified against real Supabase Postgres and Storage. Gemini connectivity
  confirmed; automatic parsing is gated on Gemini API quota/billing (free-tier
  limit 0 → HTTP 429) — owner action, not a code issue.
* V1 Refactor (product decision) — timetable upload simplified to **storage-only**
  for a fast, polished V1; automatic parsing deferred to V2. `POST /timetable/upload`
  now stores the file and returns its reference (no AI); `GET /timetable` returns the
  file + a signed view URL; `DELETE /timetable` removes it. Frontend rebuilt to
  upload/view/replace/delete (`features/timetable/TimetableUpload.tsx`); the parse/
  preview/confirm UI was removed (recoverable from git). All parser code is preserved
  behind `ENABLE_TIMETABLE_PARSING=false`; the parse/confirm/subjects routes return
  404 while disabled.
* Phase 4.5 (AI Provider Layer) implemented: `app/ai/{interfaces,providers,routers}`.
  The app talks only to the vision/chat routers; providers (Gemini vision; OpenRouter
  chat stub) are selected by `VISION_PROVIDER` / `CHAT_PROVIDER`. `timetable_parser`
  now runs through the vision router (prompts/validation/normalization unchanged).
  Config adds `VISION_PROVIDER`, `CHAT_PROVIDER`, `OPENROUTER_API_KEY`,
  `OPENROUTER_MODEL`, `ENABLE_TIMETABLE_PARSING`. Backend + frontend build/lint clean;
  live storage-only upload/replace/delete verified against Supabase with no AI called.
* Phase 7 (Assignments) implemented: full CRUD (`POST/GET/PATCH/DELETE
  /assignments`) on the pre-existing Phase 3 `assignments` schema — no new
  migration needed. `AssignmentService` validates subject ownership on
  create/edit and computes sorting (soonest due date first) and a dashboard
  grouping (Overdue/Due Today/Upcoming, pending only) in Python; `GET
  /assignments/dashboard` serves it. New `AssignmentRepository`, schemas, and
  routes registered in `main.py`. Frontend: `/assignments` page with
  `AssignmentsManager` (add/edit/delete/complete, overdue highlighting), and a
  dashboard `AssignmentsCard` that replaces the Phase 5 "Recent Tasks"
  placeholder, plus a new Quick Actions tile. Backend imports and frontend
  typecheck/lint/build verified clean.
* Phase 8 (Todo) implemented: full CRUD (`POST/GET/PATCH/DELETE /todos`) via a
  new `TodoRepository`/`TodoService`/schemas, registered in `main.py`.
  Frontend: `/todo` page with `TodoManager` (add/complete/delete), a dashboard
  `TodoCard`, and a new Quick Actions tile. Alongside it, a reusable
  `DatePicker` component was built and adopted by both Assignments and Todo
  for due-date selection, with no backend/API contract changes. Verified: CRUD
  end-to-end, dashboard integration, typecheck/lint/prod build clean, and
  manual click-through testing. Passed implementation review, pre-merge
  review, manual testing, and repository integrity verification.

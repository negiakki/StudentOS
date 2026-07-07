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

🟢 Phase 5 — Dashboard

Status: Not Started

(Phase 1 ✅ · Phase 2 ✅ · Phase 3 ✅ · Phase 4 — Timetable Upload: ✅ Complete —
upload → Supabase Storage → Gemini Vision parse → editable preview → confirm →
save. Backend + frontend build clean; live round-trips verified against real
Supabase DB and Storage. Gemini connectivity confirmed; automatic parsing is
gated on the owner enabling Gemini API quota/billing — see Phase 4 notes.)

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

Timetable Upload

Status

✅ Complete — upload → storage → parse → preview → confirm → save, verified live

Tasks

* ✅ File Upload — `POST /timetable/upload` (multipart); PDF/PNG/JPG only, 10 MB cap,
  empty/oversized/unsupported rejected with clear errors
* ✅ Storage — `StorageService` writes to Supabase Storage (service-role key, REST
  via httpx); files namespaced per user (`{user_id}/timetable/…`), re-upload upserts
* ✅ Parser — `app/ai/timetable_parser.py`: Gemini Vision (config-driven model)
  extracts subjects/days/timings/faculty/room as structured JSON; validates and
  normalizes times, drops malformed slots; never raises (falls back to manual entry)
* ✅ Preview Screen — parsed result returned as an editable `TimetablePreview`
  (nothing academic saved yet); frontend `TimetableManager` renders a full editor
* ✅ User Confirmation — user edits/adds/removes subjects & classes, client-side
  validation, then confirms
* ✅ Save Timetable — `POST /timetable` replaces any existing timetable (one per
  user): clears prior subjects (cascade) and recreates from confirmed data;
  `GET /timetable` reads it back (slots sorted by day/time)

Architecture: routes → `TimetableService` → repositories → DB, plus
`StorageService` and the AI parser; auth-scoped to the JWT user (no user id from
the client). Frontend: authed `apiFetch` (FormData-aware), `services/timetable.ts`,
`types/timetable.ts`, protected `/timetable` page.

Verified: backend imports + OpenAPI generate; `google-genai` installed; frontend
`next build` + `next lint` clean (`/timetable` route present). Live: save/read/
replace round-trip against real Supabase Postgres (with cascade cleanup); Supabase
Storage upload+delete against the live `timetables` bucket; slot validation
(end > start) enforced in schema and UI.

Owner action required to exercise automatic parsing end-to-end:
* Enable **Gemini API** billing/quota for the project — the current free-tier quota
  for `gemini-2.0-flash` is `limit: 0` (API returns HTTP 429). Connectivity and the
  request/response path are confirmed working; only quota is missing. The model is
  configurable via `GEMINI_MODEL`. Until then, upload still works and users complete
  the timetable via the manual editor (graceful fallback, Architecture §15).
* Ensure the Supabase Storage bucket named by `SUPABASE_STORAGE_BUCKET`
  (default `timetables`) exists — verified present in the current project.

---

## Phase 5

Dashboard

Status

⬜ Not Started

Tasks

* Greeting
* Today's Classes
* Weather
* Attendance Summary
* Assignments
* Todo
* Daily Brief

---

## Phase 6

Attendance

Status

⬜ Not Started

Tasks

* Attendance Setup
* Calendar View
* Mark Present
* Mark Absent
* Edit Previous Days
* Safe Skip Calculation

---

## Phase 7

Assignments

Status

⬜ Not Started

Tasks

* Create
* Edit
* Delete
* Dashboard Integration

---

## Phase 8

Todo

Status

⬜ Not Started

Tasks

* Create Task
* Complete Task
* Delete Task
* Dashboard Integration

---

## Phase 9

Coco

Status

⬜ Not Started

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

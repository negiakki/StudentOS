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

🟢 Phase 3 — Database

Status: Not Started

(Phase 1 — Repository Setup: ✅ Complete. Phase 2 — Authentication: ✅ Complete,
pending two Supabase-dashboard config steps by the owner — see Phase 2 notes.)

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

⬜ Not Started

Tasks

* SQLAlchemy Models
* Alembic Migrations
* Repository Layer
* Service Layer
* Database Connection

---

## Phase 4

Timetable Upload

Status

⬜ Not Started

Tasks

* File Upload
* Storage
* Parser
* Preview Screen
* User Confirmation
* Save Timetable

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

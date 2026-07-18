<div align="center">

# 🎓 StudentOS

**An AI-powered daily operating system for college students — with _Coco_ as the intelligent assistant.**

Instead of juggling separate apps for attendance, timetable, assignments, and planning, students get one dashboard and one AI companion that answers a single question: **"What do I need to know today?"**

[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres%20%7C%20Auth%20%7C%20Storage-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-6E56CF?logo=openai&logoColor=white)](https://openrouter.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#-license)

</div>

---

## 📖 Overview

Student life is fragmented across too many tools. Attendance lives in one portal, the timetable in a PDF, assignments in a notes app, and the daily plan in someone's head. Nothing talks to each other, and the one question that actually matters — _"what should I focus on today?"_ — never has a single answer.

**StudentOS** brings it all into one place. It tracks attendance (with safe-skip math), stores your timetable, manages assignments and todos, and surfaces everything on a single dashboard. On top of that sits **Coco**, an AI assistant you talk to in plain language: _"Can I skip DBMS tomorrow?"_, _"Summarize my day"_, _"Mark me present for OS today."_

> **Coco is the brain. Everything else is a tool.**
> Python performs every calculation; the AI only explains the results and never guesses. Writes (like marking attendance) always require your confirmation first.

---

## ✨ Features

### 🔐 Authentication
- **Google Sign-In** — one-click OAuth through Supabase Auth.
- **Email Authentication** — email + password sign-up and login, with forgot-password and reset-password flows.

### 🏠 Dashboard
- **Student overview** — attendance health, assignments, todos, and timetable at a glance.
- **Quick actions** — jump straight into the most common tasks from a single panel.

### 📊 Attendance
- **Daily attendance tracking** — mark present/absent per subject, day by day.
- **Statistics** — per-subject and overall attendance percentages against your threshold.
- **Safe skip calculations** — see exactly how many classes you can miss while staying above the required percentage. All figures are computed in Python, never stored stale.

### 🗓️ Timetable
- **Upload timetable** — upload your timetable file (validated and size-capped).
- **Store & manage** — files are stored per-user in Supabase Storage and viewable from the Timetable page.

### 📝 Assignments
- **Track assignments** — keep all coursework in one list.
- **Due dates** — grouped into overdue, due today, and upcoming.
- **Status management** — move assignments through their lifecycle with priority tagging.

### ✅ Todo
- **Daily task management** — lightweight todos with priorities and due dates, plus a "today" view for overdue, due-today, and undated items.

### 🤖 Coco AI Assistant
- **Natural language interaction** — ask about attendance, assignments, and todos in plain English.
- **Tool-based architecture** — a two-call flow selects one read-only tool per message from a fixed registry, runs it through the existing user-scoped services, then explains the result.
- **Attendance actions** — Coco can propose marking attendance; you approve it via a confirmation card before anything is written.
- **Todo actions** — Coco can propose completing a todo, again gated behind a confirmation card.
- **Assignment awareness** — Coco reads and summarizes your assignments (overdue / due today / upcoming). New assignments and todos are created through the app's own forms, by design.
- **Context-aware responses** — a combined daily snapshot lets Coco answer "summarize my day" or "what should I do first?" in a single call.

---

## 🧰 Tech Stack

**Frontend**
- Next.js 15 (App Router, PWA)
- React 19
- TypeScript
- Tailwind CSS
- Zustand · TanStack Query · Framer Motion

**Backend**
- FastAPI
- Python 3.12
- SQLAlchemy · Alembic · Pydantic

**Database & Auth**
- Supabase — PostgreSQL, Auth (Google + Email/Password), and Storage

**AI**
- OpenRouter — powers Coco's chat (default model `openai/gpt-4o-mini`)
- Google Gemini Vision — reserved for automatic timetable parsing (flag-gated off in V1; storage-only upload ships today)

**Deployment**
- Vercel (frontend)
- Render (backend)
- Supabase (database, auth, storage)

---

## 🏗️ Architecture

StudentOS is a **modular monolith**: a Next.js PWA talking to a layered FastAPI backend, with Supabase for data/auth/storage and OpenRouter for AI.

```
        ┌────────────┐
        │   Client   │  (browser / installed PWA)
        └─────┬──────┘
              │  HTTPS
        ┌─────▼──────────────┐
        │  Next.js Frontend  │  App Router, server actions, Supabase SSR
        └─────┬──────────────┘
              │  REST (JWT-authenticated)
        ┌─────▼──────────────┐
        │  FastAPI Backend   │  api → services → repositories → db
        └─────┬──────────────┘
              │
    ┌─────────┴──────────┐
    ▼                    ▼
┌─────────┐        ┌───────────────┐
│ Supabase │        │  OpenRouter   │
│ Postgres │        │  (Coco chat)  │
│ Auth     │        └───────────────┘
│ Storage  │
└─────────┘
```

Inside the backend, Coco never touches the database directly — it goes **Coco Agent → Tools → Services → Repositories → PostgreSQL**, so every AI action reuses the same user-scoped, validated business logic as the REST API. See [`Docs/03_System_Architecture.md`](Docs/03_System_Architecture.md) and [`Docs/06_Coco_V1_Design.md`](Docs/06_Coco_V1_Design.md) for the full picture.

---

## 📸 Screenshots

> Screenshots are placeholders — add images to a `Docs/screenshots/` folder and link them here.

| Screen | Preview |
| ------ | ------- |
| **Login** | _Coming soon_ |
| **Dashboard** | _Coming soon_ |
| **Attendance** | _Coming soon_ |
| **Assignments** | _Coming soon_ |
| **Todo** | _Coming soon_ |
| **Coco Assistant** | _Coming soon_ |

---

## 🚀 Local Development

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.12 (see [`.python-version`](.python-version))
- A **Supabase** project (Postgres + Auth + Storage)
- An **OpenRouter** API key (for Coco)

### 1. Clone the repository

```bash
git clone https://github.com/negiakki/StudentOS.git
cd StudentOS
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash); use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env             # then fill in real values (see below)
```

Apply database migrations (once `DATABASE_URL` is set), then start the API:

```bash
alembic upgrade head             # apply all migrations
uvicorn app.main:app --reload    # http://localhost:8000
```

- Health check: <http://localhost:8000/health>
- Interactive API docs (Swagger): <http://localhost:8000/docs>

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.local.example .env.local  # then fill in real values (see below)
npm run dev                       # http://localhost:3000
```

Open <http://localhost:3000> in your browser.

### Frontend npm scripts

| Script | Command | Description |
| ------ | ------- | ----------- |
| `npm run dev` | `next dev` | Start the dev server with hot reload |
| `npm run build` | `next build` | Production build |
| `npm run start` | `next start` | Serve the production build |
| `npm run lint` | `next lint` | Run ESLint |

---

## 🔑 Environment Variables

### Backend — `backend/.env` (copy from `.env.example`)

| Variable | Required | Description |
| -------- | :------: | ----------- |
| `ENVIRONMENT` | ✓ | Runtime environment, e.g. `development` or `production`. |
| `DEBUG` | ✓ | Enable FastAPI debug mode (`true` / `false`). |
| `CORS_ORIGINS` | ✓ | Comma-separated list of allowed frontend origins (e.g. `http://localhost:3000`). |
| `DATABASE_URL` | ✓ | Supabase Postgres connection string (`postgresql+psycopg://...`). |
| `SUPABASE_URL` | ✓ | Your Supabase project URL, used for auth (JWKS/JWT) and storage. |
| `SUPABASE_JWT_SECRET` | – | Legacy HS256 shared secret; optional fallback when the project signs JWTs symmetrically (asymmetric JWKS is preferred). |
| `SUPABASE_SERVICE_ROLE_KEY` | ✓ | Server-side-only key for Storage writes. **Never expose to the frontend.** |
| `SUPABASE_STORAGE_BUCKET` | ✓ | Storage bucket for timetable uploads (default `timetables`). |
| `VISION_PROVIDER` | ✓ | Vision provider for timetable parsing (default `gemini`). |
| `CHAT_PROVIDER` | ✓ | Chat provider for Coco (default `openrouter`). |
| `GEMINI_API_KEY` | – | API key for Gemini Vision (only needed if timetable parsing is enabled). |
| `GEMINI_MODEL` | – | Vision model used for timetable extraction (default `gemini-2.0-flash`). |
| `OPENROUTER_API_KEY` | ✓ | API key for OpenRouter — powers Coco's chat. |
| `OPENROUTER_MODEL` | ✓ | Default chat model (default `openai/gpt-4o-mini`). |
| `OPENROUTER_BASE_URL` | – | OpenRouter API base; override only for proxies/compatible gateways. |
| `WATSONX_API_KEY` | – | Reserved for an alternate provider; unused by the default configuration. |
| `ENABLE_TIMETABLE_PARSING` | – | Master switch for automatic timetable parsing. `false` in V1 (storage-only upload). |

### Frontend — `frontend/.env.local` (copy from `.env.local.example`)

| Variable | Required | Description |
| -------- | :------: | ----------- |
| `NEXT_PUBLIC_API_BASE_URL` | ✓ | Base URL of the FastAPI backend (e.g. `http://localhost:8000`). |
| `NEXT_PUBLIC_SITE_URL` | – | Public site origin for building auth redirect URLs. Optional locally (request origin is used); set in production. |
| `NEXT_PUBLIC_SUPABASE_URL` | ✓ | Supabase project URL (browser client). |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✓ | Supabase anon/public key (browser client). |

> Only `NEXT_PUBLIC_*` variables are exposed to the browser. `.env` files are git-ignored — never commit secrets.

---

## 📂 Folder Structure

```
StudentOS/
├── backend/                     # FastAPI modular monolith
│   ├── alembic/                 # Alembic migration environment + versions
│   ├── app/
│   │   ├── ai/                  # Coco AI provider layer
│   │   │   ├── interfaces/      # ChatProvider / VisionProvider protocols
│   │   │   ├── providers/       # openrouter.py, gemini.py
│   │   │   ├── routers/         # chat_router.py, vision_router.py
│   │   │   └── timetable_parser.py
│   │   ├── api/                 # HTTP routers (auth, users, attendance,
│   │   │                        #   assignments, todo, timetable, coco, health)
│   │   ├── core/                # config, security
│   │   ├── database/            # engine, session, base
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Data access layer (Postgres only)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # Business logic + Coco orchestration/tools
│   │   ├── tests/               # Backend tests
│   │   ├── utils/               # Small shared helpers
│   │   └── main.py              # FastAPI entrypoint (create_app)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # Next.js App Router PWA
│   ├── app/
│   │   ├── (auth)/              # login, signup, forgot-password, reset-password
│   │   ├── (protected)/         # dashboard, attendance, assignments, timetable, todo
│   │   └── auth/                # OAuth callback + email confirm routes
│   ├── components/              # Shared UI (auth, ui)
│   ├── features/                # Feature modules (dashboard, attendance,
│   │                            #   assignments, timetable, todo, coco)
│   ├── hooks/                   # Reusable React hooks
│   ├── lib/                     # api client, supabase clients, helpers
│   ├── services/                # Per-feature API calls
│   ├── styles/                  # Shared style assets
│   ├── types/                   # Shared TypeScript types
│   ├── middleware.ts
│   ├── next.config.mjs
│   ├── package.json
│   └── .env.local.example
├── Docs/                        # Vision, PRD, Architecture, DB & Coco design, status
├── README.md
└── .gitignore
```

---

## 🗺️ Future Roadmap

- [ ] **OCR timetable parsing** — automatic extraction of class timings from an uploaded timetable (Gemini Vision, behind `ENABLE_TIMETABLE_PARSING`).
- [ ] **Calendar integration** — sync classes, assignments, and deadlines to Google Calendar / iCal.
- [ ] **Notifications** — reminders for low attendance, due assignments, and daily plans.
- [ ] **Mobile app** — a native companion beyond the installable PWA.
- [ ] **AI scheduling** — Coco proposes an optimized daily/weekly plan.
- [ ] **Analytics** — trends and insights across attendance, workload, and productivity.
- [ ] **Smarter Coco** — richer multi-step reasoning and additional write actions.

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. **Fork** the repository.
2. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**, following the existing project conventions:
   - Business logic lives in **services**; data access lives in **repositories** — never mix them.
   - Python performs all calculations; the AI only explains results.
   - Every request is authenticated and scoped to the current user.
   - Store facts, never calculations.
4. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add your feature"
   ```
5. **Push** and open a **Pull Request** describing what you changed and why.

Please keep pull requests focused, and run `npm run lint` (frontend) before submitting.

---

## 📄 License

This project is released under the **MIT License**. You are free to use, modify, and distribute it with attribution.

---

<div align="center">

Built with ☕ and 🤖 for students who just want to know **what matters today**.

</div>

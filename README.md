# StudentOS

An AI-powered daily operating system for college students, with **Coco** as the intelligent assistant.

Instead of juggling separate apps for attendance, timetable, assignments, and planning, students interact with one dashboard and one AI companion that answers a single question: **"What do I need to know today?"**

> **Coco is the brain. Everything else is a tool.**
> Python performs the calculations. The AI explains the results. The AI never guesses.

---

## Architecture

Modular monolith. See [`Docs/03_System_Architecture.md`](Docs/03_System_Architecture.md) for the full picture.

```
Next.js Frontend (PWA)  →  FastAPI Backend  →  Coco Agent  →  Tools  →  Services  →  Repositories  →  PostgreSQL (Supabase)
```

| Layer      | Stack                                                                 |
| ---------- | --------------------------------------------------------------------- |
| Frontend   | Next.js, React, TypeScript, Tailwind CSS, Zustand, TanStack Query, Framer Motion |
| Backend    | FastAPI, Python, SQLAlchemy, Pydantic                                 |
| Database   | PostgreSQL (Supabase)                                                  |
| Auth       | Supabase Auth (Google + Email/Password)                               |
| Storage    | Supabase Storage                                                      |
| AI         | Gemini (primary), IBM watsonx (secondary)                            |
| Deploy     | Vercel (frontend), Render (backend), Supabase (DB)                   |

---

## Repository layout

```
StudentOS/
├── backend/    FastAPI modular monolith (api → services → repositories → db)
├── frontend/   Next.js App Router PWA
└── Docs/       Vision, PRD, Architecture, Database Design, Coco Agent Design, status
```

---

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash;  use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # fill in values
uvicorn app.main:app --reload
```

Health check: <http://localhost:8000/health> · API docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in values
npm run dev
```

App: <http://localhost:3000>

---

## Development roadmap

Tracked in [`Docs/PROJECT_STATUS.md`](Docs/PROJECT_STATUS.md). Build one phase at a time; do not add features outside the MVP without approval.

1. **Repository Setup** ← current
2. Authentication
3. Database
4. Timetable Upload
5. Dashboard
6. Attendance
7. Assignments
8. Todo
9. Coco
10. Testing & Deployment

---

## Engineering rules

- Coco never accesses the database directly.
- Python performs all calculations; the AI only explains results.
- Business logic lives in Services; data access lives in Repositories.
- Every request is authenticated and scoped to the current user.
- Store facts, never calculations.

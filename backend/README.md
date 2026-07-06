# StudentOS Backend

FastAPI modular monolith. Layering: **api → services → repositories → database**.
Coco (`app/ai`) orchestrates tools; it never touches the database directly.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash;  .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- Health: <http://localhost:8000/health>
- API docs (Swagger): <http://localhost:8000/docs>

## Database & migrations (Alembic)

Set `DATABASE_URL` in `.env` to your Supabase Postgres connection string, then:

```bash
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "describe change"   # after changing models
alembic downgrade -1          # roll back one migration
```

Notes:
- Use the Supabase **connection string** (Project → Settings → Database). The
  session pooler / direct connection (port 5432) is recommended for migrations.
- `ALEMBIC_DATABASE_URL` overrides `DATABASE_URL` for migration commands only
  (handy for testing against a throwaway database).
- Store facts, never calculations — attendance %/safe-skips are computed, never stored.

## Structure

```
app/
├── main.py          FastAPI entrypoint (create_app, router registration)
├── api/             HTTP routers  →  call services
├── services/        Business logic + all calculations
├── repositories/    Data access (PostgreSQL only)
├── models/          SQLAlchemy ORM models (11 tables)
├── schemas/         Pydantic request/response models
├── ai/              Coco agent + AI provider layer
├── database/        Base, engine, session (get_db)
├── core/            Config, security, shared dependencies
└── utils/           Small shared helpers

alembic/             Migration environment + versions/
alembic.ini          Alembic config (URL comes from app settings)
```

## Rules

- Business logic in services, data access in repositories — never mixed.
- Python calculates; the AI only explains.
- Every query is scoped to the authenticated user (user id comes from the JWT, never the client).

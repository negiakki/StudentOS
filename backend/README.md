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

## Structure

```
app/
├── main.py          FastAPI entrypoint (create_app, router registration)
├── api/             HTTP routers  →  call services
├── services/        Business logic + all calculations
├── repositories/    Data access (PostgreSQL only)
├── models/          SQLAlchemy ORM models
├── schemas/         Pydantic request/response models
├── ai/              Coco agent + AI provider layer
├── database/        Engine / session management
├── core/            Config, security, shared dependencies
└── utils/           Small shared helpers
```

## Rules

- Business logic in services, data access in repositories — never mixed.
- Python calculates; the AI only explains.
- Every query is scoped to the authenticated user (user id comes from the JWT, never the client).

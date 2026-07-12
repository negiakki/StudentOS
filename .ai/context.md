# StudentOS Context

## Purpose

StudentOS is an AI-powered student dashboard.

## Architecture

Frontend:
- Next.js
- TypeScript

Backend:
- FastAPI
- SQLAlchemy

Database:
- Supabase PostgreSQL

Storage:
- Supabase Storage

Authentication:
- Supabase Auth

## Principles

- Business logic belongs in Python.
- AI never accesses the database directly.
- Architecture is frozen.
- Reuse existing patterns.
- One phase at a time.
- Mobile-first.
- Current semester only.
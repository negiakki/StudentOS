# StudentOS Frontend

Next.js (App Router) PWA with TypeScript and Tailwind CSS.

## Setup

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

App: <http://localhost:3000>

## Structure

```
app/          App Router routes, layout, global styles
components/    Reusable presentational UI
features/      Feature modules (dashboard, timetable, attendance, assignments, todo, chat)
hooks/         Reusable React hooks
lib/           Low-level utilities (api.ts fetch wrapper)
services/      Per-feature API calls (built on lib/api.ts)
types/         Shared TypeScript types
styles/        Shared style assets
```

## Stack

Next.js · React · TypeScript · Tailwind CSS · Zustand · TanStack Query · Framer Motion

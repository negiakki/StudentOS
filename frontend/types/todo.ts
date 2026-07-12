/**
 * Todo domain types (Phase 8). Mirrors the backend schemas: a simple
 * checklist task, optionally due on a date, with a computed "today's tasks"
 * list for the dashboard (calculated server-side, never stored).
 */

export type Priority = "LOW" | "MEDIUM" | "HIGH";

export interface Todo {
  id: string;
  title: string;
  completed: boolean;
  due_date: string | null; // ISO date, YYYY-MM-DD
  priority: Priority;
}

export interface TodoCreate {
  title: string;
  due_date?: string | null;
  priority?: Priority;
}

export interface TodoUpdate {
  title?: string;
  due_date?: string | null;
  priority?: Priority;
  completed?: boolean;
}

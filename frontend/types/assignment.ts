/**
 * Assignment domain types (Phase 7). Mirrors the backend schemas: coursework
 * tracked by due date, with an optional subject and a computed Today/Upcoming/
 * Overdue grouping for the dashboard (calculated server-side, never stored).
 */

export type Priority = "LOW" | "MEDIUM" | "HIGH";

export type AssignmentStatus = "PENDING" | "COMPLETED";

export interface Assignment {
  id: string;
  subject_id: string | null;
  title: string;
  description: string | null;
  due_date: string | null; // ISO date, YYYY-MM-DD
  priority: Priority;
  status: AssignmentStatus;
}

export interface AssignmentCreate {
  title: string;
  description?: string | null;
  subject_id?: string | null;
  due_date?: string | null;
  priority?: Priority;
}

export interface AssignmentUpdate {
  title?: string;
  description?: string | null;
  subject_id?: string | null;
  due_date?: string | null;
  priority?: Priority;
  status?: AssignmentStatus;
}

export interface AssignmentDashboard {
  today: Assignment[];
  upcoming: Assignment[];
  overdue: Assignment[];
}

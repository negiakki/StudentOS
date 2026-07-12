/**
 * Assignments API service (Phase 7). Built on lib/api.ts. Each call needs the
 * caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type {
  Assignment,
  AssignmentCreate,
  AssignmentDashboard,
  AssignmentUpdate,
} from "@/types/assignment";

/** Pending assignments grouped into Today / Upcoming / Overdue. */
export async function getAssignmentDashboard(
  accessToken: string,
): Promise<AssignmentDashboard> {
  return apiFetch<AssignmentDashboard>("/assignments/dashboard", { accessToken });
}

/** List the user's assignments, soonest due date first. */
export async function getAssignments(
  accessToken: string,
): Promise<Assignment[]> {
  return apiFetch<Assignment[]>("/assignments", { accessToken });
}

/** A single assignment. */
export async function getAssignment(
  assignmentId: string,
  accessToken: string,
): Promise<Assignment> {
  return apiFetch<Assignment>(`/assignments/${assignmentId}`, { accessToken });
}

/** Create an assignment. Always starts PENDING. */
export async function createAssignment(
  payload: AssignmentCreate,
  accessToken: string,
): Promise<Assignment> {
  return apiFetch<Assignment>("/assignments", {
    method: "POST",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Edit an assignment, including marking it complete/pending. */
export async function updateAssignment(
  assignmentId: string,
  payload: AssignmentUpdate,
  accessToken: string,
): Promise<Assignment> {
  return apiFetch<Assignment>(`/assignments/${assignmentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Delete an assignment. Idempotent. */
export async function deleteAssignment(
  assignmentId: string,
  accessToken: string,
): Promise<{ success: boolean; removed: boolean }> {
  return apiFetch<{ success: boolean; removed: boolean }>(
    `/assignments/${assignmentId}`,
    { method: "DELETE", accessToken },
  );
}

/**
 * Todo API service (Phase 8). Built on lib/api.ts. Each call needs the
 * caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type { Todo, TodoCreate, TodoUpdate } from "@/types/todo";

/** Incomplete todos due today, overdue, or undated. */
export async function getTodosToday(accessToken: string): Promise<Todo[]> {
  return apiFetch<Todo[]>("/todos/today", { accessToken });
}

/** List the user's todos, soonest due date first. */
export async function getTodos(accessToken: string): Promise<Todo[]> {
  return apiFetch<Todo[]>("/todos", { accessToken });
}

/** A single todo. */
export async function getTodo(todoId: string, accessToken: string): Promise<Todo> {
  return apiFetch<Todo>(`/todos/${todoId}`, { accessToken });
}

/** Create a todo. Always starts incomplete. */
export async function createTodo(
  payload: TodoCreate,
  accessToken: string,
): Promise<Todo> {
  return apiFetch<Todo>("/todos", {
    method: "POST",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Edit a todo, including marking it complete/incomplete. */
export async function updateTodo(
  todoId: string,
  payload: TodoUpdate,
  accessToken: string,
): Promise<Todo> {
  return apiFetch<Todo>(`/todos/${todoId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Delete a todo. Idempotent. */
export async function deleteTodo(
  todoId: string,
  accessToken: string,
): Promise<{ success: boolean; removed: boolean }> {
  return apiFetch<{ success: boolean; removed: boolean }>(`/todos/${todoId}`, {
    method: "DELETE",
    accessToken,
  });
}

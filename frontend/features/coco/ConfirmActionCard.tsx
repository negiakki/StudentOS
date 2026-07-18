"use client";

/**
 * Confirmation card for a Coco proposed_action (Docs/06_Coco_V1_Design.md §4).
 * Coco never writes; it proposes. On Confirm we call the SAME services/*.ts the
 * forms use. The backend already resolved names→ids (todo_id, subject_id), so
 * payloads map straight onto the existing endpoints. Success reloads the page
 * so the managers re-seed from the server (they copy props into useState once).
 */

import { useState } from "react";

import { ApiError } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { markRecord } from "@/services/attendance";
import { updateTodo } from "@/services/todo";
import type { ProposedAction } from "@/types/coco";

async function getAccessToken(): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("Your session has expired. Please sign in again.");
  }
  return session.access_token;
}

/** Route one proposed_action to the existing service. Payload ids are resolved
 * server-side (coco_service._resolve_payload), so this only unpacks and calls. */
async function dispatch(action: ProposedAction, token: string): Promise<void> {
  const p = action.payload;
  switch (action.type) {
    case "complete_todo":
      await updateTodo(p.todo_id as string, { completed: true }, token);
      return;
    case "mark_attendance":
      await markRecord(
        p.subject_id as string,
        p.attendance_date as string,
        p.status as never,
        token,
      );
      return;
    default:
      throw new Error("Unknown action");
  }
}

export function ConfirmActionCard({ action }: { action: ProposedAction }) {
  const [state, setState] = useState<"idle" | "pending" | "done" | "cancelled">("idle");
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setState("pending");
    setError(null);
    try {
      await dispatch(action, await getAccessToken());
      setState("done");
      // Managers seed useState(initialX) once, so router.refresh() won't update
      // them — a full reload re-seeds from the server. ponytail: reload over a
      // cross-widget store; swap in a shared store if Coco needs live updates.
      window.location.reload();
    } catch (err) {
      setState("idle");
      setError(err instanceof ApiError || err instanceof Error ? err.message : "Couldn't do that. Please try again.");
    }
  }

  if (state === "cancelled") return null;
  if (state === "done") {
    return <p className="rounded-xl bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-950/40 dark:text-green-300">Done ✓</p>;
  }

  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-3 dark:border-neutral-700 dark:bg-neutral-950">
      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{action.summary}</p>
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={() => void confirm()}
          disabled={state === "pending"}
          className="rounded-lg bg-neutral-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
        >
          {state === "pending" ? "Working…" : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setState("cancelled")}
          disabled={state === "pending"}
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

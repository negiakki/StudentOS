"use client";

/**
 * Assignments management (Phase 7). Add coursework with an optional subject,
 * due date, and priority; edit or delete it; toggle it complete/pending. Mirrors
 * the Attendance module's add-form + inline-edit-row structure.
 */

import { useMemo, useState } from "react";

import { Card, CardHeader } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { fromISODate, todayISODate } from "@/lib/date";
import { createClient } from "@/lib/supabase/client";
import {
  createAssignment,
  deleteAssignment,
  updateAssignment,
} from "@/services/assignments";
import type {
  Assignment,
  AssignmentStatus,
  Priority,
} from "@/types/assignment";
import type { SubjectAttendance } from "@/types/attendance";

const PRIORITIES: Priority[] = ["LOW", "MEDIUM", "HIGH"];

const PRIORITY_STYLES: Record<Priority, string> = {
  LOW: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
  MEDIUM: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  HIGH: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
};

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

function messageFor(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

function formatDueDate(iso: string): string {
  return fromISODate(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function sortAssignments(items: Assignment[]): Assignment[] {
  return [...items].sort((a, b) => {
    if (!a.due_date && !b.due_date) return a.title.localeCompare(b.title);
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return a.due_date.localeCompare(b.due_date) || a.title.localeCompare(b.title);
  });
}

export function AssignmentsManager({
  initialAssignments,
  subjects,
}: {
  initialAssignments: Assignment[];
  subjects: SubjectAttendance[];
}) {
  const [assignments, setAssignments] = useState(initialAssignments);
  const [error, setError] = useState<string | null>(null);

  const subjectName = useMemo(() => {
    const map = new Map(subjects.map((s) => [s.id, s.name]));
    return (id: string | null) => (id ? map.get(id) ?? null : null);
  }, [subjects]);

  const pending = useMemo(
    () => sortAssignments(assignments.filter((a) => a.status === "PENDING")),
    [assignments],
  );
  const completed = useMemo(
    () => sortAssignments(assignments.filter((a) => a.status === "COMPLETED")),
    [assignments],
  );

  function replace(updated: Assignment) {
    setAssignments((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  async function handleAdd(payload: {
    title: string;
    description: string;
    subjectId: string;
    dueDate: string;
    priority: Priority;
  }) {
    setError(null);
    const token = await getAccessToken();
    const created = await createAssignment(
      {
        title: payload.title,
        description: payload.description || null,
        subject_id: payload.subjectId || null,
        due_date: payload.dueDate || null,
        priority: payload.priority,
      },
      token,
    );
    setAssignments((prev) => [...prev, created]);
  }

  async function handleToggleStatus(assignment: Assignment) {
    setError(null);
    try {
      const token = await getAccessToken();
      const nextStatus: AssignmentStatus =
        assignment.status === "PENDING" ? "COMPLETED" : "PENDING";
      const updated = await updateAssignment(
        assignment.id,
        { status: nextStatus },
        token,
      );
      replace(updated);
    } catch (err) {
      setError(messageFor(err));
    }
  }

  async function handleSave(
    id: string,
    payload: {
      title: string;
      description: string;
      subjectId: string;
      dueDate: string;
      priority: Priority;
    },
  ) {
    setError(null);
    const token = await getAccessToken();
    const updated = await updateAssignment(
      id,
      {
        title: payload.title,
        description: payload.description || null,
        subject_id: payload.subjectId || null,
        due_date: payload.dueDate || null,
        priority: payload.priority,
      },
      token,
    );
    replace(updated);
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      const token = await getAccessToken();
      await deleteAssignment(id, token);
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      setError(messageFor(err));
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      <AddAssignmentForm subjects={subjects} onAdd={handleAdd} onError={setError} />

      <Card>
        <CardHeader
          title="Pending"
          subtitle={
            pending.length === 0
              ? "None yet"
              : `${pending.length} assignment${pending.length === 1 ? "" : "s"}`
          }
        />
        {pending.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-neutral-500">
            No assignments yet. Add your first one above.
          </p>
        ) : (
          <ul className="divide-y divide-neutral-100 dark:divide-neutral-800">
            {pending.map((a) => (
              <AssignmentRow
                key={a.id}
                assignment={a}
                subjects={subjects}
                subjectName={subjectName(a.subject_id)}
                onToggleStatus={() => handleToggleStatus(a)}
                onSave={handleSave}
                onDelete={() => handleDelete(a.id)}
                onError={setError}
              />
            ))}
          </ul>
        )}
      </Card>

      {completed.length > 0 && (
        <Card>
          <CardHeader
            title="Completed"
            subtitle={`${completed.length} assignment${completed.length === 1 ? "" : "s"}`}
          />
          <ul className="divide-y divide-neutral-100 dark:divide-neutral-800">
            {completed.map((a) => (
              <AssignmentRow
                key={a.id}
                assignment={a}
                subjects={subjects}
                subjectName={subjectName(a.subject_id)}
                onToggleStatus={() => handleToggleStatus(a)}
                onSave={handleSave}
                onDelete={() => handleDelete(a.id)}
                onError={setError}
              />
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

const inputClass =
  "rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100 dark:placeholder:text-neutral-500";

function AddAssignmentForm({
  subjects,
  onAdd,
  onError,
}: {
  subjects: SubjectAttendance[];
  onAdd: (payload: {
    title: string;
    description: string;
    subjectId: string;
    dueDate: string;
    priority: Priority;
  }) => Promise<void>;
  onError: (msg: string | null) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<Priority>("MEDIUM");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    if (!title.trim()) return onError("Enter an assignment title.");

    setSaving(true);
    try {
      await onAdd({ title: title.trim(), description, subjectId, dueDate, priority });
      setTitle("");
      setDescription("");
      setSubjectId("");
      setDueDate("");
      setPriority("MEDIUM");
    } catch (err) {
      onError(messageFor(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Add an assignment" />
      <form onSubmit={submit} className="space-y-3 p-5">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
          className={inputClass}
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          className={`${inputClass} resize-none`}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <select
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            className={inputClass}
          >
            <option value="">No subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            type="date"
            className={inputClass}
          />
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
            className={inputClass}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p.charAt(0) + p.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
        >
          {saving ? "Adding…" : "Add"}
        </button>
      </form>
    </Card>
  );
}

function AssignmentRow({
  assignment,
  subjects,
  subjectName,
  onToggleStatus,
  onSave,
  onDelete,
  onError,
}: {
  assignment: Assignment;
  subjects: SubjectAttendance[];
  subjectName: string | null;
  onToggleStatus: () => Promise<void>;
  onSave: (
    id: string,
    payload: {
      title: string;
      description: string;
      subjectId: string;
      dueDate: string;
      priority: Priority;
    },
  ) => Promise<void>;
  onDelete: () => void;
  onError: (msg: string | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(assignment.title);
  const [description, setDescription] = useState(assignment.description ?? "");
  const [subjectId, setSubjectId] = useState(assignment.subject_id ?? "");
  const [dueDate, setDueDate] = useState(assignment.due_date ?? "");
  const [priority, setPriority] = useState<Priority>(assignment.priority);
  const [saving, setSaving] = useState(false);
  const [toggling, setToggling] = useState(false);

  const isOverdue =
    assignment.status === "PENDING" &&
    !!assignment.due_date &&
    assignment.due_date < todayISODate();

  function cancel() {
    setTitle(assignment.title);
    setDescription(assignment.description ?? "");
    setSubjectId(assignment.subject_id ?? "");
    setDueDate(assignment.due_date ?? "");
    setPriority(assignment.priority);
    setEditing(false);
    onError(null);
  }

  async function save() {
    onError(null);
    if (!title.trim()) return onError("Enter an assignment title.");

    setSaving(true);
    try {
      await onSave(assignment.id, {
        title: title.trim(),
        description,
        subjectId,
        dueDate,
        priority,
      });
      setEditing(false);
    } catch (err) {
      onError(messageFor(err));
    } finally {
      setSaving(false);
    }
  }

  async function toggle() {
    setToggling(true);
    try {
      await onToggleStatus();
    } finally {
      setToggling(false);
    }
  }

  if (editing) {
    return (
      <li className="space-y-3 px-5 py-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={inputClass}
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className={`${inputClass} w-full resize-none`}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <select
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            className={inputClass}
          >
            <option value="">No subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            type="date"
            className={inputClass}
          />
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
            className={inputClass}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p.charAt(0) + p.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="rounded-lg bg-neutral-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            {saving ? "Saving…" : "Save"}
          </button>
          <button
            type="button"
            onClick={cancel}
            className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Cancel
          </button>
        </div>
      </li>
    );
  }

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`truncate text-sm font-medium text-neutral-900 dark:text-neutral-100 ${
              assignment.status === "COMPLETED" ? "line-through opacity-60" : ""
            }`}
          >
            {assignment.title}
          </span>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLES[assignment.priority]}`}
          >
            {assignment.priority.charAt(0) + assignment.priority.slice(1).toLowerCase()}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-neutral-500">
          {subjectName && <>{subjectName} · </>}
          {assignment.due_date ? (
            <span className={isOverdue ? "text-red-600 dark:text-red-400" : ""}>
              Due {formatDueDate(assignment.due_date)}
              {isOverdue ? " (overdue)" : ""}
            </span>
          ) : (
            "No due date"
          )}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={toggle}
          disabled={toggling}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition disabled:opacity-60 ${
            assignment.status === "COMPLETED"
              ? "border border-neutral-300 text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
              : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          {assignment.status === "COMPLETED" ? "Mark Pending" : "Mark Complete"}
        </button>
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 transition hover:bg-red-50 dark:border-red-900/50 dark:hover:bg-red-950/40"
        >
          Delete
        </button>
      </div>
    </li>
  );
}

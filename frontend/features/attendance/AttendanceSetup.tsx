"use client";

/**
 * Manual attendance setup (V1). Add your semester subjects with classes
 * attended / total; the backend computes percentage and safe-skips. Subjects can
 * be edited or removed. Daily marking / calendar arrives in a later phase.
 */

import Link from "next/link";
import { useState } from "react";

import { Card, CardHeader } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import {
  addSubject,
  deleteSubject,
  updateSubject,
} from "@/services/attendance";
import type { SubjectAttendance } from "@/types/attendance";

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

export function AttendanceSetup({
  initialSubjects,
}: {
  initialSubjects: SubjectAttendance[];
}) {
  const [subjects, setSubjects] = useState(initialSubjects);
  const [error, setError] = useState<string | null>(null);

  function replace(updated: SubjectAttendance) {
    setSubjects((prev) =>
      prev
        .map((s) => (s.id === updated.id ? updated : s))
        .sort((a, b) => a.name.localeCompare(b.name)),
    );
  }

  async function handleAdd(name: string, attended: number, total: number) {
    setError(null);
    const token = await getAccessToken();
    const created = await addSubject(
      { name, attended_classes: attended, total_classes: total },
      token,
    );
    setSubjects((prev) =>
      [...prev, created].sort((a, b) => a.name.localeCompare(b.name)),
    );
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      const token = await getAccessToken();
      await deleteSubject(id, token);
      setSubjects((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(messageFor(err));
    }
  }

  async function handleSave(
    id: string,
    name: string,
    attended: number,
    total: number,
  ) {
    setError(null);
    const token = await getAccessToken();
    const updated = await updateSubject(
      id,
      { name, attended_classes: attended, total_classes: total },
      token,
    );
    replace(updated);
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      <AddSubjectForm onAdd={handleAdd} onError={setError} />

      <Card>
        <CardHeader
          title="Your subjects"
          subtitle={
            subjects.length === 0
              ? "None yet"
              : `${subjects.length} subject${subjects.length === 1 ? "" : "s"}`
          }
        />
        {subjects.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-neutral-500">
            Add your first subject above to start tracking attendance.
          </p>
        ) : (
          <ul className="divide-y divide-neutral-100 dark:divide-neutral-800">
            {subjects.map((s) => (
              <SubjectRow
                key={s.id}
                subject={s}
                onDelete={() => handleDelete(s.id)}
                onSave={handleSave}
                onError={setError}
              />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function AddSubjectForm({
  onAdd,
  onError,
}: {
  onAdd: (name: string, attended: number, total: number) => Promise<void>;
  onError: (msg: string | null) => void;
}) {
  const [name, setName] = useState("");
  const [attended, setAttended] = useState("");
  const [total, setTotal] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    onError(null);

    const a = Number(attended || 0);
    const t = Number(total || 0);
    if (!name.trim()) return onError("Enter a subject name.");
    if (a < 0 || t < 0) return onError("Counts cannot be negative.");
    if (a > t) return onError("Attended cannot be more than total classes.");

    setSaving(true);
    try {
      await onAdd(name.trim(), a, t);
      setName("");
      setAttended("");
      setTotal("");
    } catch (err) {
      onError(messageFor(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Add a subject" />
      <form
        onSubmit={submit}
        className="grid grid-cols-1 gap-3 p-5 sm:grid-cols-[1fr_auto_auto_auto]"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Subject name"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100 dark:placeholder:text-neutral-500"
        />
        <input
          value={attended}
          onChange={(e) => setAttended(e.target.value)}
          type="number"
          min={0}
          placeholder="Attended"
          className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-neutral-500 sm:w-28 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100 dark:placeholder:text-neutral-500"
        />
        <input
          value={total}
          onChange={(e) => setTotal(e.target.value)}
          type="number"
          min={0}
          placeholder="Total"
          className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-neutral-500 sm:w-28 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100 dark:placeholder:text-neutral-500"
        />
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

function SubjectRow({
  subject,
  onDelete,
  onSave,
  onError,
}: {
  subject: SubjectAttendance;
  onDelete: () => void;
  onSave: (
    id: string,
    name: string,
    attended: number,
    total: number,
  ) => Promise<void>;
  onError: (msg: string | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(subject.name);
  const [attended, setAttended] = useState(String(subject.attended_classes));
  const [total, setTotal] = useState(String(subject.total_classes));
  const [saving, setSaving] = useState(false);

  function cancel() {
    setName(subject.name);
    setAttended(String(subject.attended_classes));
    setTotal(String(subject.total_classes));
    setEditing(false);
    onError(null);
  }

  async function save() {
    onError(null);
    const a = Number(attended || 0);
    const t = Number(total || 0);
    if (!name.trim()) return onError("Enter a subject name.");
    if (a < 0 || t < 0) return onError("Counts cannot be negative.");
    if (a > t) return onError("Attended cannot be more than total classes.");

    setSaving(true);
    try {
      await onSave(subject.id, name.trim(), a, t);
      setEditing(false);
    } catch (err) {
      onError(messageFor(err));
    } finally {
      setSaving(false);
    }
  }

  if (editing) {
    return (
      <li className="flex flex-wrap items-center gap-2 px-5 py-3">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="min-w-40 flex-1 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100"
        />
        <input
          value={attended}
          onChange={(e) => setAttended(e.target.value)}
          type="number"
          min={0}
          className="w-20 rounded-lg border border-neutral-300 bg-white px-2 py-1.5 text-sm text-neutral-900 outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100"
        />
        <span className="text-neutral-400">/</span>
        <input
          value={total}
          onChange={(e) => setTotal(e.target.value)}
          type="number"
          min={0}
          className="w-20 rounded-lg border border-neutral-300 bg-white px-2 py-1.5 text-sm text-neutral-900 outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100"
        />
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
      </li>
    );
  }

  return (
    <li className="flex items-center justify-between gap-3 px-5 py-3">
      <div className="min-w-0">
        <Link
          href={`/attendance/${subject.id}`}
          className="truncate text-sm font-medium text-neutral-900 hover:underline dark:text-neutral-100"
        >
          {subject.name}
        </Link>
        <p className="mt-0.5 text-xs text-neutral-500">
          {subject.attended_classes}/{subject.total_classes} ·{" "}
          <span
            className={
              subject.meets_threshold
                ? "text-neutral-500"
                : "text-red-600 dark:text-red-400"
            }
          >
            {subject.percentage}%
          </span>
          {subject.meets_threshold && subject.total_classes > 0
            ? ` · can skip ${subject.safe_skips}`
            : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Link
          href={`/attendance/${subject.id}`}
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          Open
        </Link>
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

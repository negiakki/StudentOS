"use client";

/**
 * Timetable feature client component (Phase 4).
 *
 * Drives the full upload flow (Docs/03_System_Architecture.md §11):
 *   view saved  →  upload file  →  edit parsed preview  →  confirm & save.
 *
 * The AI-parsed preview is fully editable so the user can correct anything the
 * parser got wrong — or build a timetable by hand when parsing is unavailable
 * (Docs/03_System_Architecture.md §15). Nothing is persisted until "Save".
 */

import { useState } from "react";

import { createClient } from "@/lib/supabase/client";
import { ApiError } from "@/lib/api";
import {
  getTimetable,
  saveTimetable,
  uploadTimetable,
} from "@/services/timetable";
import {
  DAY_LABELS,
  type SubjectInput,
  type TimetableOut,
} from "@/types/timetable";

const ACCEPTED = ".pdf,.png,.jpg,.jpeg";
const ACCEPTED_MIME = ["application/pdf", "image/png", "image/jpeg"];

type Draft = {
  name: string;
  faculty: string;
  classroom: string;
  slots: {
    day_of_week: number;
    start_time: string;
    end_time: string;
    room: string;
  }[];
};

type Props = { initial: TimetableOut };

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

function outToDrafts(timetable: TimetableOut): Draft[] {
  return timetable.subjects.map((subject) => ({
    name: subject.name,
    faculty: subject.faculty ?? "",
    classroom: subject.classroom ?? "",
    slots: subject.slots.map((slot) => ({
      day_of_week: slot.day_of_week,
      start_time: slot.start_time.slice(0, 5),
      end_time: slot.end_time.slice(0, 5),
      room: slot.room ?? "",
    })),
  }));
}

export function TimetableManager({ initial }: Props) {
  const [saved, setSaved] = useState<TimetableOut>(initial);
  const [drafts, setDrafts] = useState<Draft[] | null>(null);
  const [editing, setEditing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const hasSaved = saved.subjects.length > 0;

  function beginManualEdit() {
    setError(null);
    setNotice(null);
    setDrafts(hasSaved ? outToDrafts(saved) : [emptySubject()]);
    setEditing(true);
  }

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setError(null);
    setNotice(null);

    if (!ACCEPTED_MIME.includes(file.type)) {
      setError("Unsupported file type. Upload a PDF, PNG, or JPG.");
      return;
    }

    setUploading(true);
    try {
      const token = await getAccessToken();
      const preview = await uploadTimetable(file, token);
      const parsed = preview.subjects.map((subject) => ({
        name: subject.name,
        faculty: subject.faculty ?? "",
        classroom: subject.classroom ?? "",
        slots: subject.slots.map((slot) => ({
          day_of_week: slot.day_of_week,
          start_time: slot.start_time,
          end_time: slot.end_time,
          room: slot.room ?? "",
        })),
      }));

      setDrafts(parsed.length > 0 ? parsed : [emptySubject()]);
      setEditing(true);

      if (preview.parse_error) {
        setNotice(
          "We couldn't read the timetable automatically. Enter your classes below and save.",
        );
      } else if (parsed.length === 0) {
        setNotice(
          "No classes were detected. Add them manually below, then save.",
        );
      } else {
        const pct =
          preview.parsing_confidence != null
            ? ` (about ${Math.round(preview.parsing_confidence * 100)}% confident)`
            : "";
        setNotice(
          `Parsed ${parsed.length} subject${parsed.length === 1 ? "" : "s"}${pct}. Review and edit before saving.`,
        );
      }
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleSave() {
    if (!drafts) return;
    setError(null);

    const payload = toPayload(drafts);
    const validationError = validate(payload);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    try {
      const token = await getAccessToken();
      const result = await saveTimetable({ subjects: payload }, token);
      setSaved(result);
      setDrafts(null);
      setEditing(false);
      setNotice("Timetable saved.");
      // Re-read to stay consistent with the source of truth.
      getTimetable(token).then(setSaved).catch(() => {});
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    setDrafts(null);
    setEditing(false);
    setError(null);
    setNotice(null);
  }

  // ---- Editing view ----
  if (editing && drafts) {
    return (
      <div className="space-y-5">
        <Banner error={error} notice={notice} />
        <DraftEditor drafts={drafts} onChange={setDrafts} />
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            {saving ? "Saving…" : "Save timetable"}
          </button>
          <button
            type="button"
            onClick={cancelEdit}
            disabled={saving}
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // ---- Overview view ----
  return (
    <div className="space-y-5">
      <Banner error={error} notice={notice} />

      <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-6 text-center dark:border-neutral-700 dark:bg-neutral-900">
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Upload your timetable as a PDF, PNG, or JPG. Coco reads it and lets you
          confirm the classes before saving.
        </p>
        <label className="mt-4 inline-flex cursor-pointer items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200">
          {uploading ? "Uploading…" : hasSaved ? "Upload a new timetable" : "Upload timetable"}
          <input
            type="file"
            accept={ACCEPTED}
            className="sr-only"
            disabled={uploading}
            onChange={(e) => {
              handleFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </label>
        <div className="mt-3">
          <button
            type="button"
            onClick={beginManualEdit}
            disabled={uploading}
            className="text-sm text-neutral-500 underline-offset-2 hover:underline disabled:opacity-60"
          >
            {hasSaved ? "Edit timetable manually" : "Enter timetable manually"}
          </button>
        </div>
      </div>

      {hasSaved ? (
        <SavedTimetable timetable={saved} />
      ) : (
        <p className="text-center text-sm text-neutral-500">
          No timetable yet. Upload one to get started.
        </p>
      )}
    </div>
  );
}

// ---------- Overview of the saved timetable ----------

function SavedTimetable({ timetable }: { timetable: TimetableOut }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
        Your timetable
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {timetable.subjects.map((subject) => (
          <div
            key={subject.id}
            className="rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900"
          >
            <p className="font-medium text-neutral-900 dark:text-neutral-100">
              {subject.name}
            </p>
            {(subject.faculty || subject.classroom) && (
              <p className="mt-0.5 text-xs text-neutral-500">
                {[subject.faculty, subject.classroom].filter(Boolean).join(" · ")}
              </p>
            )}
            <ul className="mt-2 space-y-1">
              {subject.slots.map((slot) => (
                <li key={slot.id} className="text-sm text-neutral-600 dark:text-neutral-400">
                  {DAY_LABELS[slot.day_of_week]} · {slot.start_time.slice(0, 5)}–
                  {slot.end_time.slice(0, 5)}
                  {slot.room ? ` · ${slot.room}` : ""}
                </li>
              ))}
              {subject.slots.length === 0 && (
                <li className="text-sm text-neutral-400">No classes scheduled</li>
              )}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- Editable draft editor ----------

function DraftEditor({
  drafts,
  onChange,
}: {
  drafts: Draft[];
  onChange: (drafts: Draft[]) => void;
}) {
  function update(next: Draft[]) {
    onChange([...next]);
  }
  function updateSubject(i: number, patch: Partial<Draft>) {
    const next = [...drafts];
    next[i] = { ...next[i], ...patch };
    update(next);
  }
  function updateSlot(si: number, sli: number, patch: Partial<Draft["slots"][number]>) {
    const next = [...drafts];
    const slots = [...next[si].slots];
    slots[sli] = { ...slots[sli], ...patch };
    next[si] = { ...next[si], slots };
    update(next);
  }

  return (
    <div className="space-y-4">
      {drafts.map((subject, si) => (
        <div
          key={si}
          className="rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900"
        >
          <div className="flex items-start justify-between gap-3">
            <input
              value={subject.name}
              onChange={(e) => updateSubject(si, { name: e.target.value })}
              placeholder="Subject name"
              className={fieldClass + " flex-1 font-medium"}
            />
            <button
              type="button"
              onClick={() => update(drafts.filter((_, idx) => idx !== si))}
              className="shrink-0 text-xs text-neutral-400 hover:text-red-600"
              aria-label="Remove subject"
            >
              Remove
            </button>
          </div>

          <div className="mt-2 grid grid-cols-2 gap-2">
            <input
              value={subject.faculty}
              onChange={(e) => updateSubject(si, { faculty: e.target.value })}
              placeholder="Faculty (optional)"
              className={fieldClass}
            />
            <input
              value={subject.classroom}
              onChange={(e) => updateSubject(si, { classroom: e.target.value })}
              placeholder="Classroom (optional)"
              className={fieldClass}
            />
          </div>

          <div className="mt-3 space-y-2">
            {subject.slots.map((slot, sli) => (
              <div key={sli} className="flex flex-wrap items-center gap-2">
                <select
                  value={slot.day_of_week}
                  onChange={(e) =>
                    updateSlot(si, sli, { day_of_week: Number(e.target.value) })
                  }
                  className={fieldClass + " w-32"}
                >
                  {Object.entries(DAY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                <input
                  type="time"
                  value={slot.start_time}
                  onChange={(e) => updateSlot(si, sli, { start_time: e.target.value })}
                  className={fieldClass + " w-28"}
                />
                <input
                  type="time"
                  value={slot.end_time}
                  onChange={(e) => updateSlot(si, sli, { end_time: e.target.value })}
                  className={fieldClass + " w-28"}
                />
                <input
                  value={slot.room}
                  onChange={(e) => updateSlot(si, sli, { room: e.target.value })}
                  placeholder="Room"
                  className={fieldClass + " w-24"}
                />
                <button
                  type="button"
                  onClick={() =>
                    updateSubject(si, {
                      slots: subject.slots.filter((_, idx) => idx !== sli),
                    })
                  }
                  className="text-xs text-neutral-400 hover:text-red-600"
                  aria-label="Remove class"
                >
                  ✕
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                updateSubject(si, { slots: [...subject.slots, emptySlot()] })
              }
              className="text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200"
            >
              + Add class
            </button>
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={() => update([...drafts, emptySubject()])}
        className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
      >
        + Add subject
      </button>
    </div>
  );
}

function Banner({ error, notice }: { error: string | null; notice: string | null }) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
        {error}
      </div>
    );
  }
  if (notice) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-2.5 text-sm text-neutral-700 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300">
        {notice}
      </div>
    );
  }
  return null;
}

// ---------- helpers ----------

const fieldClass =
  "rounded-lg border border-neutral-300 bg-white px-2.5 py-1.5 text-sm text-neutral-900 outline-none transition focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100";

function emptySlot() {
  return { day_of_week: 1, start_time: "09:00", end_time: "10:00", room: "" };
}

function emptySubject(): Draft {
  return { name: "", faculty: "", classroom: "", slots: [emptySlot()] };
}

function toPayload(drafts: Draft[]): SubjectInput[] {
  return drafts
    .map((subject) => ({
      name: subject.name.trim(),
      faculty: subject.faculty.trim() || null,
      classroom: subject.classroom.trim() || null,
      slots: subject.slots.map((slot) => ({
        day_of_week: slot.day_of_week,
        start_time: slot.start_time,
        end_time: slot.end_time,
        room: slot.room.trim() || null,
      })),
    }))
    .filter((subject) => subject.name.length > 0);
}

function validate(subjects: SubjectInput[]): string | null {
  if (subjects.length === 0) {
    return "Add at least one subject with a name before saving.";
  }
  for (const subject of subjects) {
    for (const slot of subject.slots) {
      if (!slot.start_time || !slot.end_time) {
        return `Every class needs a start and end time (check "${subject.name}").`;
      }
      if (slot.end_time <= slot.start_time) {
        return `A class in "${subject.name}" ends before it starts.`;
      }
    }
  }
  return null;
}

function messageFor(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

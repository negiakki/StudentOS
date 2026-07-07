"use client";

/**
 * Timetable upload (V1 — storage-only).
 *
 * Flow: upload a PDF/PNG/JPG → it is stored in Supabase Storage → the uploaded
 * file is displayed. The user can replace or delete it. No parsing, no preview,
 * no confirmation — the upload feels instant.
 *
 * Automatic parsing is postponed to V2; the backend keeps that code behind
 * ENABLE_TIMETABLE_PARSING.
 */

import { useState } from "react";

import { ApiError } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import {
  deleteTimetableFile,
  getTimetableFile,
  uploadTimetableFile,
} from "@/services/timetable";
import type { TimetableFile } from "@/types/timetable";

const ACCEPTED = ".pdf,.png,.jpg,.jpeg";
const ACCEPTED_MIME = ["application/pdf", "image/png", "image/jpeg"];

type Props = { initialFile: TimetableFile | null };

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

export function TimetableUpload({ initialFile }: Props) {
  const [file, setFile] = useState<TimetableFile | null>(initialFile);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(picked: File | undefined) {
    if (!picked) return;
    setError(null);

    if (!ACCEPTED_MIME.includes(picked.type)) {
      setError("Unsupported file type. Upload a PDF, PNG, or JPG.");
      return;
    }

    setUploading(true);
    try {
      const token = await getAccessToken();
      const uploaded = await uploadTimetableFile(picked, token);
      setFile(uploaded);
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete() {
    setError(null);
    setDeleting(true);
    try {
      const token = await getAccessToken();
      await deleteTimetableFile(token);
      setFile(null);
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setDeleting(false);
    }
  }

  async function refresh() {
    try {
      const token = await getAccessToken();
      const state = await getTimetableFile(token);
      setFile(state.file);
    } catch {
      // Non-critical: keep showing what we have.
    }
  }

  const busy = uploading || deleting;

  return (
    <div className="space-y-5">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-6 text-center dark:border-neutral-700 dark:bg-neutral-900">
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Upload your timetable as a PDF, PNG, or JPG. It&apos;s saved instantly and
          shown below.
        </p>
        <label
          className={`mt-4 inline-flex items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 ${
            busy ? "cursor-not-allowed opacity-60" : "cursor-pointer"
          }`}
        >
          {uploading
            ? "Uploading…"
            : file
              ? "Replace timetable"
              : "Upload timetable"}
          <input
            type="file"
            accept={ACCEPTED}
            className="sr-only"
            disabled={busy}
            onChange={(e) => {
              handleFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </label>
      </div>

      {file ? (
        <TimetableFileView
          file={file}
          onDelete={handleDelete}
          onRetryUrl={refresh}
          deleting={deleting}
        />
      ) : (
        <p className="text-center text-sm text-neutral-500">
          No timetable uploaded yet.
        </p>
      )}
    </div>
  );
}

function TimetableFileView({
  file,
  onDelete,
  onRetryUrl,
  deleting,
}: {
  file: TimetableFile;
  onDelete: () => void;
  onRetryUrl: () => void;
  deleting: boolean;
}) {
  const isPdf = file.mime_type === "application/pdf";
  const uploadedAt = formatDate(file.uploaded_at);

  return (
    <div className="space-y-3 rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium text-neutral-900 dark:text-neutral-100">
            {file.filename}
          </p>
          <p className="text-xs text-neutral-500">
            {isPdf ? "PDF" : "Image"}
            {uploadedAt ? ` · uploaded ${uploadedAt}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {file.view_url && (
            <a
              href={file.view_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            >
              Open
            </a>
          )}
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-60 dark:border-red-900/50 dark:hover:bg-red-950/40"
          >
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-neutral-200 dark:border-neutral-800">
        {file.view_url ? (
          isPdf ? (
            <iframe
              src={file.view_url}
              title={file.filename}
              className="h-[70vh] w-full bg-neutral-50 dark:bg-neutral-950"
            />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={file.view_url}
              alt={file.filename}
              className="max-h-[70vh] w-full bg-neutral-50 object-contain dark:bg-neutral-950"
            />
          )
        ) : (
          <div className="p-6 text-center text-sm text-neutral-500">
            Preview link expired.{" "}
            <button
              type="button"
              onClick={onRetryUrl}
              className="underline underline-offset-2 hover:text-neutral-900 dark:hover:text-neutral-200"
            >
              Refresh
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function messageFor(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

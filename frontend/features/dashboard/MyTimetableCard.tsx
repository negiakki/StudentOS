/**
 * My Timetable (dashboard). Shows the uploaded timetable file inline so it is
 * visible without navigating away. View-only: replacing happens on the timetable
 * page. Image uploads render as an image; PDFs render in an embedded frame.
 *
 * V1 stand-in: in V2 (parsing re-enabled) this card is replaced by "Today's
 * Classes". It is intentionally self-contained so the dashboard only swaps this
 * one component — no wider refactor needed.
 */

import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";
import type { TimetableFile } from "@/types/timetable";

export function MyTimetableCard({ file }: { file: TimetableFile | null }) {
  if (!file) {
    return (
      <Card>
        <CardHeader title="My Timetable" />
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Upload your class timetable to see it here.
          </p>
          <Link
            href="/timetable"
            className="mt-4 inline-flex items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Upload timetable
          </Link>
        </div>
      </Card>
    );
  }

  const isPdf = file.mime_type === "application/pdf";

  return (
    <Card className="overflow-hidden">
      <CardHeader
        title="My Timetable"
        subtitle={isPdf ? "PDF" : "Image"}
        action={
          <Link
            href="/timetable"
            className="text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
          >
            Replace
          </Link>
        }
      />

      <div className="border-b border-neutral-100 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950">
        {file.view_url ? (
          isPdf ? (
            <iframe
              src={file.view_url}
              title={file.filename}
              className="h-[420px] w-full"
            />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={file.view_url}
              alt={file.filename}
              className="max-h-[420px] w-full object-contain"
            />
          )
        ) : (
          <div className="px-5 py-10 text-center text-sm text-neutral-500">
            Preview unavailable.{" "}
            <Link
              href="/timetable"
              className="underline underline-offset-2 hover:text-neutral-900 dark:hover:text-neutral-200"
            >
              Open timetable
            </Link>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-3 px-5 py-3">
        <span className="truncate text-xs text-neutral-500">
          {file.filename}
        </span>
        {file.view_url && (
          <a
            href={file.view_url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
          >
            Open full
          </a>
        )}
      </div>
    </Card>
  );
}

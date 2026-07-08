/**
 * Attendance Overview (dashboard). Presentational: renders the backend-computed
 * overview (percentage, safe-skips, threshold warnings) or a set-up CTA when the
 * user has no subjects yet. All figures come from the backend — no math here.
 */

import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";
import type { AttendanceOverview as Overview } from "@/types/attendance";

export function AttendanceOverview({ overview }: { overview: Overview | null }) {
  if (!overview || overview.subject_count === 0) {
    return (
      <Card>
        <CardHeader title="Attendance" />
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Add your semester subjects to start tracking attendance.
          </p>
          <Link
            href="/attendance"
            className="mt-4 inline-flex items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Set up attendance
          </Link>
        </div>
      </Card>
    );
  }

  const { overall_percentage, threshold, below_threshold_count } = overview;
  const overallOk = overall_percentage >= threshold;

  return (
    <Card>
      <CardHeader
        title="Attendance"
        subtitle={`Target ${threshold}%`}
        action={
          <Link
            href="/attendance"
            className="text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
          >
            Manage
          </Link>
        }
      />

      <div className="flex items-center gap-4 px-5 py-4">
        <div>
          <span
            className={`text-3xl font-semibold tabular-nums ${
              overallOk
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {overall_percentage}%
          </span>
          <p className="mt-0.5 text-xs text-neutral-500">
            {overview.attended_total}/{overview.total_total} classes ·{" "}
            {overview.subject_count} subject
            {overview.subject_count === 1 ? "" : "s"}
          </p>
        </div>
        {below_threshold_count > 0 && (
          <span className="ml-auto rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 dark:bg-red-950/40 dark:text-red-300">
            {below_threshold_count} below target
          </span>
        )}
      </div>

      <ul className="divide-y divide-neutral-100 border-t border-neutral-100 dark:divide-neutral-800 dark:border-neutral-800">
        {overview.subjects.map((s) => {
          const pct = Math.min(100, Math.max(0, s.percentage));
          return (
            <li key={s.id} className="px-5 py-3">
              <div className="flex items-baseline justify-between gap-3">
                <span className="truncate text-sm font-medium text-neutral-800 dark:text-neutral-200">
                  {s.name}
                </span>
                <span
                  className={`shrink-0 text-sm tabular-nums ${
                    s.meets_threshold
                      ? "text-neutral-600 dark:text-neutral-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {s.percentage}%
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
                <div
                  className={`h-full rounded-full ${
                    s.meets_threshold ? "bg-emerald-500" : "bg-red-500"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <p className="mt-1.5 text-xs text-neutral-500">
                {s.attended_classes}/{s.total_classes} ·{" "}
                {s.meets_threshold
                  ? `can skip ${s.safe_skips}`
                  : "below target"}
              </p>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

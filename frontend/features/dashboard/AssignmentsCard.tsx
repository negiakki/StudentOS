/**
 * Assignments (dashboard). Replaces the Recent Tasks placeholder now that
 * Phase 7 exists. Presentational: renders the backend-computed Today/Upcoming/
 * Overdue grouping, or a set-up CTA when there's nothing pending.
 */

import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";
import { fromISODate } from "@/lib/date";
import type { Assignment, AssignmentDashboard } from "@/types/assignment";

const MAX_ITEMS_PER_SECTION = 4;

function dueLabel(a: Assignment): string {
  if (!a.due_date) return "No due date";
  return fromISODate(a.due_date).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
  });
}

function Section({
  title,
  items,
  tone,
}: {
  title: string;
  items: Assignment[];
  tone: "red" | "amber" | "neutral";
}) {
  if (items.length === 0) return null;

  const toneClass =
    tone === "red"
      ? "text-red-600 dark:text-red-400"
      : tone === "amber"
        ? "text-amber-700 dark:text-amber-400"
        : "text-neutral-500";

  return (
    <div className="px-5 py-3">
      <p className={`text-xs font-semibold uppercase tracking-wide ${toneClass}`}>
        {title} · {items.length}
      </p>
      <ul className="mt-2 space-y-1.5">
        {items.slice(0, MAX_ITEMS_PER_SECTION).map((a) => (
          <li key={a.id} className="flex items-baseline justify-between gap-3">
            <span className="truncate text-sm text-neutral-800 dark:text-neutral-200">
              {a.title}
            </span>
            <span className="shrink-0 text-xs text-neutral-500">{dueLabel(a)}</span>
          </li>
        ))}
        {items.length > MAX_ITEMS_PER_SECTION && (
          <li className="text-xs text-neutral-400">
            +{items.length - MAX_ITEMS_PER_SECTION} more
          </li>
        )}
      </ul>
    </div>
  );
}

export function AssignmentsCard({
  dashboard,
}: {
  dashboard: AssignmentDashboard | null;
}) {
  const isEmpty =
    !dashboard ||
    (dashboard.today.length === 0 &&
      dashboard.upcoming.length === 0 &&
      dashboard.overdue.length === 0);

  if (isEmpty) {
    return (
      <Card>
        <CardHeader title="Assignments" />
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-neutral-500">
            Your assignments will show up here.
          </p>
          <Link
            href="/assignments"
            className="mt-4 inline-flex items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Add an assignment
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Assignments"
        action={
          <Link
            href="/assignments"
            className="text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
          >
            Manage
          </Link>
        }
      />
      <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
        <Section title="Overdue" items={dashboard.overdue} tone="red" />
        <Section title="Due Today" items={dashboard.today} tone="amber" />
        <Section title="Upcoming" items={dashboard.upcoming} tone="neutral" />
      </div>
    </Card>
  );
}

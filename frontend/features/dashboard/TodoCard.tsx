/**
 * Today's tasks (dashboard). Presentational: renders the backend-computed
 * "today" list (overdue, due today, or undated — incomplete only), or a
 * set-up CTA when there's nothing to show.
 */

import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";
import { fromISODate, todayISODate } from "@/lib/date";
import type { Todo } from "@/types/todo";

const MAX_ITEMS = 5;

function dueLabel(t: Todo): string {
  if (!t.due_date) return "No due date";
  const isOverdue = t.due_date < todayISODate();
  const label = fromISODate(t.due_date).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
  });
  return isOverdue ? `${label} (overdue)` : label;
}

export function TodoCard({ todos }: { todos: Todo[] | null }) {
  const isEmpty = !todos || todos.length === 0;

  if (isEmpty) {
    return (
      <Card>
        <CardHeader title="Today's Tasks" />
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-neutral-500">
            Your tasks will show up here.
          </p>
          <Link
            href="/todo"
            className="mt-4 inline-flex items-center rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Add a task
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Today's Tasks"
        action={
          <Link
            href="/todo"
            className="text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
          >
            Manage
          </Link>
        }
      />
      <ul className="divide-y divide-neutral-100 px-5 py-1 dark:divide-neutral-800">
        {todos.slice(0, MAX_ITEMS).map((t) => (
          <li key={t.id} className="flex items-baseline justify-between gap-3 py-2">
            <span className="truncate text-sm text-neutral-800 dark:text-neutral-200">
              {t.title}
            </span>
            <span
              className={`shrink-0 text-xs ${
                t.due_date && t.due_date < todayISODate()
                  ? "text-red-600 dark:text-red-400"
                  : "text-neutral-500"
              }`}
            >
              {dueLabel(t)}
            </span>
          </li>
        ))}
        {todos.length > MAX_ITEMS && (
          <li className="py-2 text-xs text-neutral-400">
            +{todos.length - MAX_ITEMS} more
          </li>
        )}
      </ul>
    </Card>
  );
}

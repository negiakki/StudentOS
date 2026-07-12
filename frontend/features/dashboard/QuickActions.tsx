/**
 * Quick Actions (dashboard). The dashboard's navigation hub for V1 — jump to the
 * timetable and attendance surfaces. Only links to features that exist today.
 */

import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";

type Action = { href: string; label: string; hint: string; icon: string };

const ACTIONS: Action[] = [
  {
    href: "/timetable",
    label: "Timetable",
    hint: "Upload or replace",
    icon: "🗓️",
  },
  {
    href: "/attendance",
    label: "Attendance",
    hint: "Add subjects & update",
    icon: "✅",
  },
  {
    href: "/assignments",
    label: "Assignments",
    hint: "Track coursework by due date",
    icon: "📝",
  },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader title="Quick Actions" />
      <div className="grid grid-cols-1 gap-2 p-3 sm:grid-cols-2 lg:grid-cols-1">
        {ACTIONS.map((a) => (
          <Link
            key={a.href}
            href={a.href}
            className="flex items-center gap-3 rounded-xl border border-neutral-200 px-4 py-3 transition hover:border-neutral-300 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/50"
          >
            <span className="text-lg" aria-hidden>
              {a.icon}
            </span>
            <span>
              <span className="block text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {a.label}
              </span>
              <span className="block text-xs text-neutral-500">{a.hint}</span>
            </span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

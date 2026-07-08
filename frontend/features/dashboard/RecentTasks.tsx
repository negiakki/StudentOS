/**
 * Recent Tasks (dashboard). To-dos land in a later phase, so V1 shows a calm
 * placeholder rather than an empty widget. Kept as its own component so the list
 * can drop in later without touching the dashboard layout.
 */

import { Card, CardHeader } from "@/components/ui/Card";

export function RecentTasks() {
  return (
    <Card>
      <CardHeader title="Recent Tasks" />
      <div className="px-5 py-6 text-center">
        <p className="text-sm text-neutral-500">
          Your to-dos will show up here.
        </p>
        <p className="mt-1 text-xs text-neutral-400 dark:text-neutral-600">
          Coming in a later update.
        </p>
      </div>
    </Card>
  );
}

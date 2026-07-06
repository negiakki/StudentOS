import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Good to see you 👋
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          You&apos;re signed in as {user?.email}.
        </p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Authentication is working. The full dashboard — Daily Brief, today&apos;s
          classes, attendance, assignments, and todos — arrives in later phases.
          Next up: onboarding and the database layer.
        </p>
      </div>
    </div>
  );
}

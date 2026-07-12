import Link from "next/link";

import { TodoManager } from "@/features/todo/TodoManager";
import { createClient } from "@/lib/supabase/server";
import { getTodos } from "@/services/todo";
import type { Todo } from "@/types/todo";

export default async function TodoPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  let initialTodos: Todo[] = [];
  if (session?.access_token) {
    initialTodos = await getTodos(session.access_token).catch(() => []);
  }

  return (
    <div className="space-y-6">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 text-sm text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
      >
        ← Dashboard
      </Link>
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Todo
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Track your checklist tasks. Mark them complete once you&apos;re
          done, or edit them as things change.
        </p>
      </div>

      <TodoManager initialTodos={initialTodos} />
    </div>
  );
}

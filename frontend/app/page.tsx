import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="max-w-xl space-y-6">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            StudentOS
          </h1>
          <p className="text-lg text-neutral-500 dark:text-neutral-400">
            Your AI-powered daily operating system for college. Meet{" "}
            <span className="font-semibold text-neutral-800 dark:text-neutral-200">
              Coco
            </span>
            , the assistant that answers one question every morning:{" "}
            <em>&ldquo;What do I need to know today?&rdquo;</em>
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/signup"
            className="rounded-lg bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-neutral-300 px-5 py-2.5 text-sm font-medium text-neutral-900 transition hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-100 dark:hover:bg-neutral-900"
          >
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}

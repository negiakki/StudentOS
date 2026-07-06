export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="max-w-xl space-y-4">
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
        <p className="text-sm text-neutral-400">
          Phase 1 — Repository Setup complete. Authentication is next.
        </p>
      </div>
    </main>
  );
}

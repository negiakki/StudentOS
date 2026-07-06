import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-50 p-4 dark:bg-neutral-950">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <Link
            href="/"
            className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100"
          >
            StudentOS
          </Link>
        </div>
        <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
          {children}
        </div>
      </div>
    </main>
  );
}

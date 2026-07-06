import Link from "next/link";

import { AuthMessage } from "@/components/auth/AuthMessage";
import { inputClass, labelClass } from "@/components/auth/field-styles";
import { SubmitButton } from "@/components/auth/SubmitButton";

import { login, signInWithGoogle } from "../actions";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string; redirectedFrom?: string }>;
}) {
  const { error, message, redirectedFrom } = await searchParams;

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          Welcome back
        </h1>
        <p className="text-sm text-neutral-500">Sign in to continue to StudentOS</p>
      </div>

      <AuthMessage error={error} message={message} />

      <form action={signInWithGoogle}>
        <SubmitButton variant="secondary" pendingText="Redirecting…">
          Continue with Google
        </SubmitButton>
      </form>

      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-neutral-200 dark:bg-neutral-800" />
        <span className="text-xs text-neutral-400">or</span>
        <span className="h-px flex-1 bg-neutral-200 dark:bg-neutral-800" />
      </div>

      <form action={login} className="space-y-4">
        <input type="hidden" name="redirectedFrom" value={redirectedFrom ?? ""} />
        <div>
          <label htmlFor="email" className={labelClass}>
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className={inputClass}
          />
        </div>
        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="password" className={labelClass}>
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200"
            >
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            className={inputClass}
          />
        </div>
        <SubmitButton pendingText="Signing in…">Sign in</SubmitButton>
      </form>

      <p className="text-center text-sm text-neutral-500">
        Don&apos;t have an account?{" "}
        <Link
          href="/signup"
          className="font-medium text-neutral-900 hover:underline dark:text-neutral-100"
        >
          Sign up
        </Link>
      </p>
    </div>
  );
}

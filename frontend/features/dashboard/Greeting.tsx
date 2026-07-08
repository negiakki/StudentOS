"use client";

/**
 * Time-of-day greeting. The greeting text depends on the viewer's local clock,
 * so it is computed after mount to avoid an SSR/CSR hydration mismatch.
 */

import { useEffect, useState } from "react";

function greetingFor(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("Welcome back");

  useEffect(() => {
    setGreeting(greetingFor(new Date().getHours()));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
        {greeting}, {name} 👋
      </h1>
      <p className="mt-1 text-sm text-neutral-500">
        Here&apos;s your StudentOS at a glance.
      </p>
    </div>
  );
}

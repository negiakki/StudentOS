"use client";

/**
 * Small theme selector for the top nav: System (default), Light, Dark.
 * The choice is persisted to localStorage and applied by toggling the `dark`
 * class on <html> (see lib/theme.ts). The initial class is set pre-paint by the
 * blocking script in the root layout, so this only drives runtime changes.
 */

import { useEffect, useState } from "react";

import {
  applyTheme,
  getStoredTheme,
  storeTheme,
  type Theme,
} from "@/lib/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  // Hydrate from storage after mount to avoid a server/client mismatch.
  useEffect(() => {
    setTheme(getStoredTheme());
    setMounted(true);
  }, []);

  // While on "system", follow live OS preference changes.
  useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  function change(next: Theme) {
    setTheme(next);
    storeTheme(next);
    applyTheme(next);
  }

  return (
    <select
      aria-label="Theme"
      value={mounted ? theme : "system"}
      onChange={(e) => change(e.target.value as Theme)}
      className="rounded-lg border border-neutral-300 bg-white px-2 py-1.5 text-sm text-neutral-700 outline-none transition hover:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800"
    >
      <option value="system">System</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  );
}

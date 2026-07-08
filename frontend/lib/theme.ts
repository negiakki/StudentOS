/**
 * App theme: System (default), Light, Dark.
 *
 * The choice is stored in localStorage and applied by toggling the `dark` class
 * on <html> (Tailwind darkMode: "class"). "system" follows the OS preference.
 * The initial class is set by a blocking script in the root layout to avoid a
 * flash of the wrong theme; these helpers drive runtime changes.
 */

export type Theme = "system" | "light" | "dark";

export const THEME_KEY = "studentos-theme";
export const THEMES: Theme[] = ["system", "light", "dark"];

export function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const value = window.localStorage.getItem(THEME_KEY);
  return value === "light" || value === "dark" || value === "system"
    ? value
    : "system";
}

export function systemPrefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

/** Toggle the `dark` class to match the effective theme. */
export function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  const dark = theme === "dark" || (theme === "system" && systemPrefersDark());
  document.documentElement.classList.toggle("dark", dark);
}

export function storeTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch {
    // Private mode / storage disabled — the theme still applies for this session.
  }
}

import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudentOS",
  description:
    "An AI-powered daily operating system for college students, with Coco as your intelligent assistant.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0a",
};

// Runs before paint to set the `dark` class from the stored preference (or the
// OS setting when "system"/unset), avoiding a flash of the wrong theme. Keep in
// sync with lib/theme.ts (THEME_KEY, applyTheme).
const themeScript = `(function(){try{var t=localStorage.getItem('studentos-theme');var dark=t==='dark'||((t==='system'||t===null)&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',dark);}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}

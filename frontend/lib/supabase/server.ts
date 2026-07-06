/**
 * Server Supabase client (Server Components, Server Actions, Route Handlers).
 *
 * Built on the getAll/setAll cookie contract (the current @supabase/ssr API).
 * In Next.js 15 `cookies()` is async, so this factory is async too. Always call
 * it inside the request — never store the client in module scope (a warm server
 * instance could leak one user's session into another's request).
 */

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // `setAll` can be called from a Server Component, where writing
            // cookies is disallowed. Safe to ignore: the middleware refreshes
            // the session and writes the cookies on every request.
          }
        },
      },
    },
  );
}

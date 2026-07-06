/**
 * Browser Supabase client (Client Components).
 *
 * Uses @supabase/ssr's createBrowserClient, which persists the session in
 * cookies (shared with the server) and uses the PKCE flow by default.
 * Create a fresh client per use — never hoist to module scope.
 */

import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}

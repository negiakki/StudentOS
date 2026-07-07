/**
 * Thin fetch wrapper around the StudentOS backend API.
 * Feature services (services/*) build on this; components never call fetch directly.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiFetchOptions = RequestInit & {
  /** Supabase access token; sent as `Authorization: Bearer` when present. */
  accessToken?: string;
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { accessToken, headers, body, ...rest } = options;

  const finalHeaders: Record<string, string> = { ...(headers as Record<string, string>) };

  // Let the browser set the multipart boundary for FormData; only default to
  // JSON for other body types.
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  if (!isFormData && !("Content-Type" in finalHeaders)) {
    finalHeaders["Content-Type"] = "application/json";
  }
  if (accessToken) {
    finalHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    body,
    headers: finalHeaders,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await extractError(res));
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

/** Prefer the API's `{ detail }` error body; fall back to the status text. */
async function extractError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // non-JSON body
  }
  return `API ${res.status}: ${res.statusText}`;
}

export { API_BASE_URL };

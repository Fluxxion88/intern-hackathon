// Fetch helpers. Same-origin /api/* is rewritten to localhost:8000 by next.config.ts
// so cookies stay same-origin; credentials included everywhere anyway.

export const MOCK_FLAG = process.env.NEXT_PUBLIC_MOCK === "1";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path, { credentials: "include", cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`);
  return res.json();
}

export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(path, { method: "POST", credentials: "include", body: form });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

/** True when we should run from fixtures: flag set, or the job id is the demo id. */
export function isMockJob(jobId: string): boolean {
  return MOCK_FLAG || jobId === "demo";
}

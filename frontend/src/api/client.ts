// Thin fetch wrapper. All calls are same-origin under "/api", which:
//   - dev:  Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.ts)
//   - prod: nginx proxies /api -> the FastAPI service (see deploy/nginx.conf)
//
// Not used while the app runs on mock data, but ready for when api/habits.ts
// switches its implementations over to real requests.

const BASE = '/api'

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error((detail as { detail?: string }).detail ?? `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

// Simulate network latency so loading states are exercised in mock mode.
export const mockDelay = (ms = 250) => new Promise((r) => setTimeout(r, ms))

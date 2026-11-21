// Thin client for server.py. Every decision (safety, summaries, costs) is made server-side.
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');

export async function api(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(`${API_BASE}/api/${path}`, {
    method,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const money = (n) => `$${Number(n || 0).toFixed(2)}`;
export const money0 = (n) => `$${Math.round(Number(n || 0)).toLocaleString()}`;
export const timeAgo = (iso) => {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  return mins < 1 ? 'just now' : mins < 60 ? `${mins} min ago` : `${Math.round(mins / 60)} h ago`;
};

// sessionStorage can throw (private mode, blocked storage): never let that break the app.
export const session = {
  get(key) {
    try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; }
  },
  set(key, value) {
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ }
  },
  clear(key) {
    try { sessionStorage.setItem(key, 'null'); } catch { /* storage unavailable */ }
  },
};

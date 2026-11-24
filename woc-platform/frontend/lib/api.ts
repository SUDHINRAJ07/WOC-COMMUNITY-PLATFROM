/**
 * Resolves the backend API base URL using explicit environment variables and intelligent defaults.
 * Configured via NEXT_PUBLIC_API_URL (e.g. "http://localhost:8317/api" or "https://api.yourdomain.com/api").
 */
export const getApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '');
  }
  if (typeof window === 'undefined') {
    return 'http://127.0.0.1:8317/api';
  }
  const { protocol, hostname, port } = window.location;
  // If running Next.js dev server on 3000 or static server on 4317, connect to backend on 8317:
  if (['4317', '3000', '3001'].includes(port)) {
    return `${protocol}//${hostname}:8317/api`;
  }
  // If running behind a reverse proxy or deployed with /api path:
  return `${protocol}//${hostname}${port ? `:${port}` : ''}/api`;
};

/**
 * Checks whether explicit demo mode is requested.
 * Configured via NEXT_PUBLIC_DEMO_MODE=true.
 * Defaults to false so the real backend database is always utilized.
 */
export const isDemoMode = (): boolean => {
  if (process.env.NEXT_PUBLIC_DEMO_MODE !== undefined) {
    return process.env.NEXT_PUBLIC_DEMO_MODE.toLowerCase() === 'true';
  }
  return false;
};

// Backwards-compatible helper
export const localBackend = () => !isDemoMode();

let csrf = '';

export async function api(path: string, method = 'GET', data?: unknown) {
  const base = getApiBase();
  try {
    if (method !== 'GET' && !csrf) {
      const r = await fetch(base + '/csrf/', { credentials: 'include' });
      if (!r.ok) {
        throw new Error(`Failed to initialize session security (HTTP ${r.status}).`);
      }
      const csrfData = await r.json();
      csrf = csrfData.csrfToken || '';
    }

    const r = await fetch(base + path, {
      method,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrf ? { 'X-CSRFToken': csrf } : {}),
      },
      ...(data ? { body: JSON.stringify(data) } : {}),
    });

    const json = await r.json().catch(() => ({}));
    if (!r.ok) {
      throw Object.assign(new Error(json.error || json.detail || `Server returned error (${r.status}). Please try again.`), {status:r.status,data:json});
    }
    if (json.csrfToken) {
      csrf = json.csrfToken;
    }
    return json;
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
      throw new Error(`Cannot connect to WOC backend at ${base}. Please ensure the backend server is running.`);
    }
    throw err;
  }
}

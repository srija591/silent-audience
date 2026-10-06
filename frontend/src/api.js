// In production the backend is a separate Render service: set VITE_API_URL at build time. Empty = same origin (dev proxy).
export const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
export const getToken = () => localStorage.getItem('sa_token')
export const setAuth = (t, u) => { localStorage.setItem('sa_token', t); localStorage.setItem('sa_user', JSON.stringify(u)) }
export const clearAuth = () => { localStorage.removeItem('sa_token'); localStorage.removeItem('sa_user') }
export const getUser = () => { try { return JSON.parse(localStorage.getItem('sa_user')) } catch { return null } }

export async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) }
  const t = getToken()
  if (t) headers.Authorization = `Bearer ${t}`
  let body = opts.body
  if (body && !(body instanceof FormData)) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(body) }
  const r = await fetch(API_BASE + '/api' + path, { method: opts.method || 'GET', headers, body })
  if (r.status === 401 && t) { clearAuth(); window.location.href = '/' }
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || 'Request failed')
  return data
}

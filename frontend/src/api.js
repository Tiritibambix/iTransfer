import { clearToken } from './storage'

// Wraps fetch for authenticated admin API calls. A 401 means the JWT has
// expired or is invalid -- without this, callers were treating the error
// body (e.g. {"error": "..."}) as if it were the expected response shape,
// which crashed rendering downstream (e.g. calling .filter() on it).
export async function authFetch(url, options = {}) {
  const r = await fetch(url, options)
  if (r.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Session expired')
  }
  return r
}

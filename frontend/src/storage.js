// localStorage can throw (not just return null) under some privacy-hardened
// browser configurations -- e.g. strict tracking protection or storage
// partitioning blocking access for a given site. This app has no error
// boundary, so an uncaught exception here would silently blank the whole
// page on render. Every access goes through these wrappers instead.
const AUTH_TOKEN_KEY = 'authToken'

export function getToken() {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    return true
  } catch {
    return false
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY)
  } catch {
    // Already inaccessible -- nothing to clear.
  }
}

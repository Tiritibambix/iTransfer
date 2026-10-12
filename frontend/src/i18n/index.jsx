import { createContext, useContext, useState, useCallback, useMemo } from 'react'
import { getLang, setLang as persistLang } from '../storage'
import en from './en.json'
import fr from './fr.json'
import es from './es.json'
import de from './de.json'
import it from './it.json'

// Native labels so each language is recognizable in its own script.
export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'fr', label: 'Français' },
  { code: 'es', label: 'Español' },
  { code: 'de', label: 'Deutsch' },
  { code: 'it', label: 'Italiano' },
]
export const SUPPORTED = LANGUAGES.map(l => l.code)
export const DEFAULT_LANG = 'en'

const DICTS = { en, fr, es, de, it }

export function detectLanguage() {
  const stored = getLang()
  if (stored && SUPPORTED.includes(stored)) return stored
  const nav = ((navigator.language || (navigator.languages && navigator.languages[0]) || '')
    .toLowerCase().split('-')[0])
  return SUPPORTED.includes(nav) ? nav : DEFAULT_LANG
}

function translate(dict, key, vars) {
  let str = dict[key]
  if (str == null) str = DICTS[DEFAULT_LANG][key]
  if (str == null) return key
  if (vars) {
    for (const k of Object.keys(vars)) {
      str = str.split(`{${k}}`).join(String(vars[k]))
    }
  }
  return str
}

const I18nContext = createContext(null)

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(detectLanguage)

  // persist defaults to true for an explicit user choice; pages that render in
  // a language chosen for them (e.g. the download page using the transfer's
  // language) pass persist:false so they don't overwrite the viewer's own pref.
  const setLang = useCallback((next, { persist = true } = {}) => {
    if (!SUPPORTED.includes(next)) return
    setLangState(next)
    if (persist) persistLang(next)
    try { document.documentElement.lang = next } catch { /* non-DOM env */ }
  }, [])

  const t = useCallback(
    (key, vars) => translate(DICTS[lang] || DICTS[DEFAULT_LANG], key, vars),
    [lang],
  )

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useT() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useT must be used within I18nProvider')
  return ctx
}

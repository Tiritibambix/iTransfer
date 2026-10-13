import { useState, useRef, useEffect } from 'react'
import { useT, LANGUAGES } from './i18n'

// The one and only language control in the app, rendered once inside
// <Header>. A compact trigger (language code) + a small custom dropdown --
// never a native <select>, which renders full language names at a
// different size/weight than the surrounding nav buttons and ends up
// looking like a stray form control instead of part of the nav.
export default function LanguageSelector() {
  const { lang, setLang, t } = useT()
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  const current = LANGUAGES.find(l => l.code === lang) || LANGUAGES[0]

  useEffect(() => {
    if (!open) return
    const closeOnOutsideClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    const closeOnEscape = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', closeOnOutsideClick)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  return (
    <div className="lang-switcher" ref={rootRef}>
      <button
        type="button"
        className="lang-trigger"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('lang.label')}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M2 12h20M12 2a15.3 15.3 0 010 20 15.3 15.3 0 010-20z"/>
        </svg>
        {current.code.toUpperCase()}
      </button>

      {open && (
        <div className="lang-menu" role="listbox">
          {LANGUAGES.map(l => (
            <button
              type="button"
              key={l.code}
              role="option"
              aria-selected={l.code === lang}
              className={`lang-menu__item${l.code === lang ? ' lang-menu__item--active' : ''}`}
              onClick={() => { setLang(l.code); setOpen(false) }}
            >
              {l.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

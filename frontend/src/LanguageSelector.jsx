import { useT, LANGUAGES } from './i18n'

export default function LanguageSelector({ persist = true }) {
  const { lang, setLang, t } = useT()
  return (
    <select
      className="input"
      style={{ width: 'auto', minWidth: 0, paddingTop: '6px', paddingBottom: '6px' }}
      value={lang}
      onChange={e => setLang(e.target.value, { persist })}
      aria-label={t('lang.label')}
    >
      {LANGUAGES.map(l => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  )
}

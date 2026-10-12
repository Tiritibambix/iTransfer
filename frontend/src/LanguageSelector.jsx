import { useT, LANGUAGES } from './i18n'

// The one and only language control in the app, rendered once inside
// <Header>. There is a single language concept (the viewer's own UI
// language, used for everything they see and everything they send), so
// this component never takes a "which language context" prop.
export default function LanguageSelector() {
  const { lang, setLang, t } = useT()
  return (
    <select
      className="input lang-select"
      value={lang}
      onChange={e => setLang(e.target.value)}
      aria-label={t('lang.label')}
    >
      {LANGUAGES.map(l => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  )
}

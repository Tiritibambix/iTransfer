import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import banner from './assets/banner.png'
import { setToken } from './storage'
import { useT } from './i18n'
import LanguageSelector from './LanguageSelector'

const backendUrl = window.BACKEND_URL

export default function Login() {
  const navigate = useNavigate()
  const { t } = useT()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    setLoading(true); setError('')
    try {
      const r = await fetch(`${backendUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (r.ok) {
        const data = await r.json()
        if (setToken(data.token)) {
          navigate('/')
        } else {
          setError(t('login.storageBlocked'))
        }
      } else if (r.status === 429) {
        setError(t('login.tooMany'))
      } else {
        setError(t('login.invalid'))
      }
    } catch {
      setError(t('login.unreachable'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page page--centered">
      <div className="container--narrow">

        <div className="flex justify-end mb-4">
          <LanguageSelector />
        </div>

        <div className="text-center mb-8">
          <img src={banner} alt="iTransfer" className="app-logo" style={{ margin: '0 auto' }} />
        </div>

        <div className="card">
          <div className="card__body flex-col gap-4">
            <h1 className="text-center" style={{ fontSize: 'var(--font-lg)', fontWeight: 600, marginBottom: 'var(--sp-2)' }}>
              {t('login.title')}
            </h1>

            <form onSubmit={handleSubmit} className="flex-col gap-4">
              <div className="field">
                <label className="field__label" htmlFor="username">{t('login.username')}</label>
                <input id="username" className="input" type="text" autoComplete="username"
                  value={username} onChange={e => setUsername(e.target.value)} disabled={loading} required />
              </div>
              <div className="field">
                <label className="field__label" htmlFor="password">{t('login.password')}</label>
                <input id="password" className="input" type="password" autoComplete="current-password"
                  value={password} onChange={e => setPassword(e.target.value)} disabled={loading} required />
              </div>

              {error && <div className="toast toast--error">{error}</div>}

              <button type="submit" className="btn btn--primary btn--full btn--lg" disabled={loading}>
                {loading ? <><span className="spinner" />{t('login.signingIn')}</> : t('login.signIn')}
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  )
}

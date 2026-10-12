import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getToken, clearToken } from './storage'
import { authFetch } from './api'
import { useT } from './i18n'
import Header from './Header'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function formatDate(iso, locale) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString(locale, {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 5000)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div className={`toast toast--${type} mb-4`} role="alert">
      <span style={{ flex: 1 }}>{message}</span>
      <button className="file-item__remove" onClick={onClose}>✕</button>
    </div>
  )
}

// Notification outcome badge: status is null (never attempted), 'pending',
// 'sent', or 'failed'. The error message (if any) shows as a hover tooltip.
function NotifBadge({ label, n }) {
  const cls = n.status === 'sent' ? 'badge--success'
            : n.status === 'failed' ? 'badge--error'
            : 'badge--muted'
  const text = n.status === 'sent' ? `${label} ✓`
             : n.status === 'failed' ? `${label} ✗`
             : `${label} …`
  return <span className={`badge ${cls}`} title={n.error || ''}>{text}</span>
}

// ---- Tab: Transfers ----
function TransfersTab({ token }) {
  const { t, lang } = useT()
  const [transfers, setTransfers] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const frontendUrl = window.location.origin

  const load = useCallback(() => {
    setLoading(true)
    authFetch(`${backendUrl}/api/transfers`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => { setTransfers(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => { setToast({ message: t('admin.loadFailed'), type: 'error' }); setLoading(false) })
  }, [token, t])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!confirm(t('admin.confirmDelete'))) return
    setDeleting(id)
    try {
      const r = await authFetch(`${backendUrl}/api/transfers/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (r.ok) {
        setTransfers(prev => prev.filter(tr => tr.id !== id))
        setToast({ message: t('admin.deleted'), type: 'success' })
      } else {
        setToast({ message: t('admin.deleteFailed'), type: 'error' })
      }
    } catch {
      setToast({ message: t('admin.networkError'), type: 'error' })
    } finally {
      setDeleting(null)
    }
  }

  const active = transfers.filter(tr => !tr.expired)
  const expired = transfers.filter(tr => tr.expired)

  return (
    <div>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between mb-6" style={{ flexWrap: 'wrap', gap: 'var(--sp-3)' }}>
        <p className="text-sm text-muted">
          {t('admin.activeExpired', { active: active.length, expired: expired.length })}
        </p>
        <button className="btn btn--ghost btn--sm" onClick={load} disabled={loading}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          {t('admin.refresh')}
        </button>
      </div>

      {loading ? (
        <div className="text-center mt-6"><span className="spinner" style={{ width: 28, height: 28 }} /></div>
      ) : transfers.length === 0 ? (
        <div className="text-center text-muted mt-6">{t('admin.noTransfers')}</div>
      ) : (
        <div className="transfer-list">
          {transfers.map(tr => (
            <div key={tr.id} className={`transfer-card${tr.expired ? ' transfer-card--expired' : ''}`}>
              <div className="transfer-card__header">
                <span>
                  {tr.expired
                    ? <span className="badge badge--muted">{t('admin.expired')}</span>
                    : tr.downloaded
                      ? <span className="badge badge--success">{t('admin.downloaded')}</span>
                      : <span className="badge badge--muted">{t('admin.pending')}</span>
                  }
                </span>
                <div className="flex gap-2">
                  {!tr.expired && (
                    <a
                      href={`${frontendUrl}/download/${tr.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn--ghost btn--sm"
                      title={t('admin.openDownload')}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                        <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                      </svg>
                    </a>
                  )}
                  <button
                    className="btn btn--danger btn--sm"
                    onClick={() => handleDelete(tr.id)}
                    disabled={deleting === tr.id}
                    aria-label={t('admin.delete')}
                  >
                    {deleting === tr.id
                      ? <span className="spinner" style={{ width: 12, height: 12 }} />
                      : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                        </svg>
                    }
                  </button>
                </div>
              </div>
              <div className="transfer-card__body">
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.from')}</span>
                  <span className="transfer-card__value">{tr.sender_email}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.to')}</span>
                  <span className="transfer-card__value">{tr.recipient_email}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.files')}</span>
                  <span className="transfer-card__value">{tr.file_count} · {formatSize(tr.total_size)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.created')}</span>
                  <span className="transfer-card__value">{formatDate(tr.created_at, lang)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.expires')}</span>
                  <span className="transfer-card__value">{formatDate(tr.expires_at, lang)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">{t('admin.notifications')}</span>
                  <span className="transfer-card__value flex gap-2" style={{ flexWrap: 'wrap' }}>
                    <NotifBadge label={t('admin.recipient')} n={tr.notifications.recipient} />
                    <NotifBadge label={t('admin.sender')} n={tr.notifications.sender} />
                    {tr.downloaded && <NotifBadge label={t('admin.downloadAlert')} n={tr.notifications.download} />}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Deliverability check result row: status is 'pass', 'warn', or 'fail'.
function ResultRow({ label, result }) {
  if (!result) return null
  const cls = result.status === 'pass' ? 'badge--success'
            : result.status === 'warn' ? 'badge--muted'
            : 'badge--error'
  return (
    <div className="transfer-card__row">
      <span className="transfer-card__label">{label}</span>
      <span className="transfer-card__value transfer-card__value--wrap">
        <span className={`badge ${cls}`}>{result.status.toUpperCase()}</span>{' '}
        {result.message}
      </span>
    </div>
  )
}

// ---- Tab: SMTP ----
function SmtpTab({ token }) {
  const { t, lang } = useT()
  const [cfg, setCfg] = useState({
    smtpServer: '', smtpPort: '', smtpUser: '', smtpPassword: '', smtpSenderEmail: ''
  })
  const [toast, setToast] = useState(null)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [dkimSelector, setDkimSelector] = useState('')
  const [checking, setChecking] = useState(false)
  const [checkResult, setCheckResult] = useState(null)

  useEffect(() => {
    authFetch(`${backendUrl}/api/get-smtp-settings`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setCfg(prev => ({ ...prev, ...data })) })
      .catch(() => {})
  }, [token])

  const handleSave = async () => {
    setSaving(true)
    try {
      const r = await authFetch(`${backendUrl}/api/save-smtp-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(cfg),
      })
      const data = await r.json()
      if (r.ok) setToast({ message: t('admin.configSaved'), type: 'success' })
      else setToast({ message: data.error || t('admin.configError'), type: 'error' })
    } catch {
      setToast({ message: t('admin.networkError'), type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const r = await authFetch(`${backendUrl}/api/test-smtp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ language: lang }),
      })
      const data = await r.json()
      if (r.ok) setToast({ message: t('admin.testOk'), type: 'success' })
      else setToast({ message: data.error || t('admin.testFailed'), type: 'error' })
    } catch {
      setToast({ message: t('admin.networkError'), type: 'error' })
    } finally {
      setTesting(false)
    }
  }

  const handleCheckDeliverability = async () => {
    setChecking(true)
    setCheckResult(null)
    try {
      const r = await authFetch(`${backendUrl}/api/check-deliverability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ dkim_selector: dkimSelector }),
      })
      const data = await r.json()
      if (r.ok) setCheckResult(data)
      else setToast({ message: data.error || t('admin.checkFailed'), type: 'error' })
    } catch {
      setToast({ message: t('admin.networkError'), type: 'error' })
    } finally {
      setChecking(false)
    }
  }

  const field = (label, key, type = 'text', placeholder = '') => (
    <div className="field">
      <label className="field__label">{label}</label>
      <input
        className="input"
        type={type}
        placeholder={placeholder}
        value={cfg[key]}
        onChange={e => setCfg(prev => ({ ...prev, [key]: e.target.value }))}
      />
    </div>
  )

  return (
    <div>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <div className="smtp-grid">
        {field(t('admin.smtpServer'), 'smtpServer', 'text', 'ssl0.ovh.net')}
        {field(t('admin.port'), 'smtpPort', 'text', '465')}
        {field(t('admin.username'), 'smtpUser', 'text', 'user@domain.com')}
        {field(t('admin.password'), 'smtpPassword', 'password', '••••••••')}
        {field(t('admin.senderEmail'), 'smtpSenderEmail', 'email', 'no-reply@domain.com')}
        <div className="smtp-actions">
          <button className="btn btn--primary" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
            {saving ? <><span className="spinner" />{t('admin.saving')}</> : t('admin.save')}
          </button>
          <button className="btn btn--ghost" style={{ flex: 1 }} onClick={handleTest} disabled={testing}>
            {testing ? <><span className="spinner" />{t('admin.testing')}</> : t('admin.test')}
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--sp-6)' }}>
        <div className="card__body">
          <p className="text-sm text-muted mb-4">
            {t('admin.deliverabilityHint', { domain: cfg.smtpSenderEmail?.split('@')[1] || t('admin.yourDomain') })}
          </p>
          <div className="field mb-4">
            <label className="field__label">{t('admin.dkimSelector')}</label>
            <input
              className="input"
              type="text"
              placeholder={t('admin.dkimPlaceholder')}
              value={dkimSelector}
              onChange={e => setDkimSelector(e.target.value)}
            />
          </div>
          <button className="btn btn--primary" onClick={handleCheckDeliverability} disabled={checking}>
            {checking ? <><span className="spinner" />{t('admin.checking')}</> : t('admin.checkDeliverability')}
          </button>

          {checkResult && (
            <div className="transfer-card mt-4">
              <div className="transfer-card__body">
                <ResultRow label="SPF" result={checkResult.spf} />
                <ResultRow label="DMARC" result={checkResult.dmarc} />
                {checkResult.dkim && <ResultRow label="DKIM" result={checkResult.dkim} />}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ---- Main Admin page ----
export default function Admin() {
  const navigate = useNavigate()
  const { t } = useT()
  const token = getToken() || ''
  const [tab, setTab] = useState('transfers')

  const logout = () => {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="page">
      <div className="container--wide">

        <Header>
          <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>
            {t('nav.back')}
          </button>
          <button className="btn btn--danger btn--sm" onClick={logout}>
            {t('nav.signOut')}
          </button>
        </Header>

        <div className="card">
          <div className="card__body">
            <div className="tabs">
              <button className={`tab${tab === 'transfers' ? ' tab--active' : ''}`} onClick={() => setTab('transfers')}>
                {t('admin.tabTransfers')}
              </button>
              <button className={`tab${tab === 'smtp' ? ' tab--active' : ''}`} onClick={() => setTab('smtp')}>
                {t('admin.tabSmtp')}
              </button>
            </div>

            {tab === 'transfers' && <TransfersTab token={token} />}
            {tab === 'smtp' && <SmtpTab token={token} />}
          </div>
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import banner from './assets/banner.png'
import { getToken, clearToken } from './storage'
import { authFetch } from './api'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
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
      .catch(() => { setToast({ message: 'Failed to load transfers.', type: 'error' }); setLoading(false) })
  }, [token])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!confirm('Delete this transfer and its file?')) return
    setDeleting(id)
    try {
      const r = await authFetch(`${backendUrl}/api/transfers/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (r.ok) {
        setTransfers(prev => prev.filter(t => t.id !== id))
        setToast({ message: 'Transfer deleted.', type: 'success' })
      } else {
        setToast({ message: 'Failed to delete transfer.', type: 'error' })
      }
    } catch {
      setToast({ message: 'Network error.', type: 'error' })
    } finally {
      setDeleting(null)
    }
  }

  const active = (Array.isArray(transfers) ? transfers : []).filter(t => !t.expired)
  const expired = (Array.isArray(transfers) ? transfers : []).filter(t => t.expired)

  return (
    <div>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between mb-6" style={{ flexWrap: 'wrap', gap: 'var(--sp-3)' }}>
        <p className="text-sm text-muted">
          {active.length} active · {expired.length} expired
        </p>
        <button className="btn btn--ghost btn--sm" onClick={load} disabled={loading}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center mt-6"><span className="spinner" style={{ width: 28, height: 28 }} /></div>
      ) : transfers.length === 0 ? (
        <div className="text-center text-muted mt-6">No transfers yet.</div>
      ) : (
        <div className="transfer-list">
          {transfers.map(t => (
            <div key={t.id} className={`transfer-card${t.expired ? ' transfer-card--expired' : ''}`}>
              <div className="transfer-card__header">
                <span>
                  {t.expired
                    ? <span className="badge badge--muted">Expired</span>
                    : t.downloaded
                      ? <span className="badge badge--success">Downloaded</span>
                      : <span className="badge badge--muted">Pending</span>
                  }
                </span>
                <div className="flex gap-2">
                  {!t.expired && (
                    <a
                      href={`${frontendUrl}/download/${t.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn--ghost btn--sm"
                      title="Open download page"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                        <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                      </svg>
                    </a>
                  )}
                  <button
                    className="btn btn--danger btn--sm"
                    onClick={() => handleDelete(t.id)}
                    disabled={deleting === t.id}
                    aria-label="Delete"
                  >
                    {deleting === t.id
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
                  <span className="transfer-card__label">From</span>
                  <span className="transfer-card__value">{t.sender_email}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">To</span>
                  <span className="transfer-card__value">{t.recipient_email}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">Files</span>
                  <span className="transfer-card__value">{t.file_count} · {formatSize(t.total_size)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">Created</span>
                  <span className="transfer-card__value">{formatDate(t.created_at)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">Expires</span>
                  <span className="transfer-card__value">{formatDate(t.expires_at)}</span>
                </div>
                <div className="transfer-card__row">
                  <span className="transfer-card__label">Notifications</span>
                  <span className="transfer-card__value flex gap-2" style={{ flexWrap: 'wrap' }}>
                    <NotifBadge label="Recipient" n={t.notifications.recipient} />
                    <NotifBadge label="Sender" n={t.notifications.sender} />
                    {t.downloaded && <NotifBadge label="Download alert" n={t.notifications.download} />}
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
      if (r.ok) setToast({ message: 'Configuration saved.', type: 'success' })
      else setToast({ message: data.error || 'Error saving configuration.', type: 'error' })
    } catch {
      setToast({ message: 'Network error.', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const r = await authFetch(`${backendUrl}/api/test-smtp`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await r.json()
      if (r.ok) setToast({ message: 'Test successful! Check your inbox.', type: 'success' })
      else setToast({ message: data.error || 'Test failed.', type: 'error' })
    } catch {
      setToast({ message: 'Network error.', type: 'error' })
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
      else setToast({ message: data.error || 'Check failed.', type: 'error' })
    } catch {
      setToast({ message: 'Network error.', type: 'error' })
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
        {field('SMTP Server', 'smtpServer', 'text', 'ssl0.ovh.net')}
        {field('Port', 'smtpPort', 'text', '465')}
        {field('Username', 'smtpUser', 'text', 'user@domain.com')}
        {field('Password', 'smtpPassword', 'password', '••••••••')}
        {field('Sender email', 'smtpSenderEmail', 'email', 'no-reply@domain.com')}
        <div className="smtp-actions">
          <button className="btn btn--primary" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
            {saving ? <><span className="spinner" />Saving…</> : 'Save'}
          </button>
          <button className="btn btn--ghost" style={{ flex: 1 }} onClick={handleTest} disabled={testing}>
            {testing ? <><span className="spinner" />Testing…</> : 'Test'}
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--sp-6)' }}>
        <div className="card__body">
          <p className="text-sm text-muted mb-4">
            Re-check SPF/DMARC (and DKIM, if you provide your provider's selector)
            for <strong>{cfg.smtpSenderEmail?.split('@')[1] || 'your domain'}</strong>.
            DNS records drift over time -- re-run this rather than relying on a
            check you did a while ago, especially after any DNS or registrar change.
          </p>
          <div className="field mb-4">
            <label className="field__label">DKIM selector (optional)</label>
            <input
              className="input"
              type="text"
              placeholder="e.g. selector1, google, default"
              value={dkimSelector}
              onChange={e => setDkimSelector(e.target.value)}
            />
          </div>
          <button className="btn btn--primary" onClick={handleCheckDeliverability} disabled={checking}>
            {checking ? <><span className="spinner" />Checking…</> : 'Check deliverability'}
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
  const token = getToken() || ''
  const [tab, setTab] = useState('transfers')

  const logout = () => {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="page">
      <div className="container--wide glow-accent">

        <header className="app-header mb-8">
          <img src={banner} alt="iTransfer" className="app-logo" />
          <div className="flex gap-2">
            <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>
              ← Back
            </button>
            <button className="btn btn--danger btn--sm" onClick={logout}>
              Sign out
            </button>
          </div>
        </header>

        <div className="card">
          <div className="card__body">
            <div className="tabs">
              <button className={`tab${tab === 'transfers' ? ' tab--active' : ''}`} onClick={() => setTab('transfers')}>
                Transfers
              </button>
              <button className={`tab${tab === 'smtp' ? ' tab--active' : ''}`} onClick={() => setTab('smtp')}>
                SMTP Settings
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

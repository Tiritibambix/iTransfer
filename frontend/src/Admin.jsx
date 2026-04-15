import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import banner from './assets/banner.png'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', {
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

// ---- Tab: Transfers ----
function TransfersTab({ token }) {
  const [transfers, setTransfers] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const frontendUrl = window.location.origin

  const load = useCallback(() => {
    setLoading(true)
    fetch(`${backendUrl}/api/transfers`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => { setTransfers(data); setLoading(false) })
      .catch(() => { setToast({ message: 'Erreur de chargement.', type: 'error' }); setLoading(false) })
  }, [token])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!confirm('Supprimer ce transfert et son fichier ?')) return
    setDeleting(id)
    try {
      const r = await fetch(`${backendUrl}/api/transfers/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (r.ok) {
        setTransfers(prev => prev.filter(t => t.id !== id))
        setToast({ message: 'Transfert supprimé.', type: 'success' })
      } else {
        setToast({ message: 'Erreur lors de la suppression.', type: 'error' })
      }
    } catch {
      setToast({ message: 'Erreur réseau.', type: 'error' })
    } finally {
      setDeleting(null)
    }
  }

  const active = transfers.filter(t => !t.expired)
  const expired = transfers.filter(t => t.expired)

  return (
    <div>
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between mb-6" style={{ flexWrap: 'wrap', gap: 'var(--sp-3)' }}>
        <p className="text-sm text-muted">
          {active.length} actif{active.length !== 1 ? 's' : ''} · {expired.length} expiré{expired.length !== 1 ? 's' : ''}
        </p>
        <button className="btn btn--ghost btn--sm" onClick={load} disabled={loading}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Actualiser
        </button>
      </div>

      {loading ? (
        <div className="text-center mt-6"><span className="spinner" style={{ width: 28, height: 28 }} /></div>
      ) : transfers.length === 0 ? (
        <div className="text-center text-muted mt-6">Aucun transfert.</div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="table-wrap hide-mobile-table">
            <table>
              <thead>
                <tr>
                  <th>Expéditeur</th>
                  <th>Destinataire</th>
                  <th>Fichiers</th>
                  <th>Taille</th>
                  <th>Créé</th>
                  <th>Expire</th>
                  <th>Statut</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {transfers.map(t => (
                  <tr key={t.id}>
                    <td className="truncate" style={{ maxWidth: 160 }} title={t.sender_email}>{t.sender_email}</td>
                    <td className="truncate" style={{ maxWidth: 160 }} title={t.recipient_email}>{t.recipient_email}</td>
                    <td>{t.file_count}</td>
                    <td>{formatSize(t.total_size)}</td>
                    <td>{formatDate(t.created_at)}</td>
                    <td>{formatDate(t.expires_at)}</td>
                    <td>
                      {t.expired
                        ? <span className="badge badge--muted">Expiré</span>
                        : t.downloaded
                          ? <span className="badge badge--success">Téléchargé</span>
                          : <span className="badge badge--muted">En attente</span>
                      }
                    </td>
                    <td>
                      <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
                        {!t.expired && (
                          <a
                            href={`${frontendUrl}/download/${t.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn--ghost btn--sm"
                            title="Voir la page de téléchargement"
                          >
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                          </a>
                        )}
                        <button
                          className="btn btn--danger btn--sm"
                          onClick={() => handleDelete(t.id)}
                          disabled={deleting === t.id}
                          aria-label="Supprimer"
                        >
                          {deleting === t.id
                            ? <span className="spinner" style={{ width: 12, height: 12 }} />
                            : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                              </svg>
                          }
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="transfer-cards">
            {transfers.map(t => (
              <div key={t.id} className="transfer-card">
                <div className="flex items-center justify-between mb-3">
                  <span>
                    {t.expired
                      ? <span className="badge badge--muted">Expiré</span>
                      : t.downloaded
                        ? <span className="badge badge--success">Téléchargé</span>
                        : <span className="badge badge--muted">En attente</span>
                    }
                  </span>
                  <div className="flex gap-2">
                    {!t.expired && (
                      <a
                        href={`${frontendUrl}/download/${t.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn--ghost btn--sm"
                        title="Voir la page de téléchargement"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                      </a>
                    )}
                    <button
                      className="btn btn--danger btn--sm"
                      onClick={() => handleDelete(t.id)}
                      disabled={deleting === t.id}
                    >
                      {deleting === t.id
                        ? <span className="spinner" style={{ width: 12, height: 12 }} />
                        : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                          </svg>
                      }
                    </button>
                  </div>
                </div>
                <div className="flex-col gap-2 text-sm">
                  <div><span className="text-muted">De : </span>{t.sender_email}</div>
                  <div><span className="text-muted">À : </span>{t.recipient_email}</div>
                  <div><span className="text-muted">Taille : </span>{formatSize(t.total_size)} · {t.file_count} fichier{t.file_count > 1 ? 's' : ''}</div>
                  <div><span className="text-muted">Expire : </span>{formatDate(t.expires_at)}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ---- Tab: SMTP ----
function SmtpTab({ token }) {
  const [cfg, setCfg] = useState({ smtpServer: '', smtpPort: '', smtpUser: '', smtpPassword: '', smtpSenderEmail: '' })
  const [toast, setToast] = useState(null)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    fetch(`${backendUrl}/api/get-smtp-settings`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => setCfg(prev => ({ ...prev, ...data })))
      .catch(() => {})
  }, [token])

  const handleSave = async () => {
    setSaving(true)
    try {
      const r = await fetch(`${backendUrl}/api/save-smtp-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(cfg),
      })
      const data = await r.json()
      if (r.ok) setToast({ message: 'Configuration sauvegardée.', type: 'success' })
      else setToast({ message: data.error || 'Erreur.', type: 'error' })
    } catch {
      setToast({ message: 'Erreur réseau.', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const r = await fetch(`${backendUrl}/api/test-smtp`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await r.json()
      if (r.ok) setToast({ message: 'Test réussi ! Vérifiez votre boîte mail.', type: 'success' })
      else setToast({ message: data.error || 'Test échoué.', type: 'error' })
    } catch {
      setToast({ message: 'Erreur réseau.', type: 'error' })
    } finally {
      setTesting(false)
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
        {field('Serveur SMTP', 'smtpServer', 'text', 'ssl0.ovh.net')}
        {field('Port', 'smtpPort', 'text', '465')}
        {field('Utilisateur', 'smtpUser', 'text', 'user@domain.com')}
        {field('Mot de passe', 'smtpPassword', 'password', '••••••••')}
        {field('Email expéditeur', 'smtpSenderEmail', 'email', 'no-reply@domain.com')}
        <div className="smtp-actions">
          <button className="btn btn--primary" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
            {saving ? <><span className="spinner" />Sauvegarde…</> : 'Enregistrer'}
          </button>
          <button className="btn btn--ghost" style={{ flex: 1 }} onClick={handleTest} disabled={testing}>
            {testing ? <><span className="spinner" />Test…</> : 'Tester'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---- Main Admin page ----
export default function Admin() {
  const navigate = useNavigate()
  const token = localStorage.getItem('authToken') || ''
  const [tab, setTab] = useState('transfers')

  const logout = () => {
    localStorage.removeItem('authToken')
    navigate('/login')
  }

  return (
    <div className="page">
      <div className="container--wide glow-accent">

        <header className="app-header mb-8">
          <img src={banner} alt="iTransfer" className="app-logo" />
          <div className="flex gap-2">
            <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>
              ← Retour
            </button>
            <button className="btn btn--danger btn--sm" onClick={logout}>
              Déconnexion
            </button>
          </div>
        </header>

        <div className="card">
          <div className="card__body">
            <div className="tabs">
              <button className={`tab${tab === 'transfers' ? ' tab--active' : ''}`} onClick={() => setTab('transfers')}>
                Transferts
              </button>
              <button className={`tab${tab === 'smtp' ? ' tab--active' : ''}`} onClick={() => setTab('smtp')}>
                Configuration SMTP
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

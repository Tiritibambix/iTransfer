import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import banner from './assets/iTransfer Bannière.png'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 6000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div className={`toast toast--${type} mb-4`} role="alert">
      <span style={{ flex: 1 }}>{message}</span>
      <button className="file-item__remove" onClick={onClose} aria-label="Fermer">✕</button>
    </div>
  )
}

export default function App() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [recipientEmail, setRecipientEmail] = useState('')
  const [senderEmail, setSenderEmail] = useState('')
  const [expirationDays, setExpirationDays] = useState(7)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [phase, setPhase] = useState('') // 'uploading' | 'done'
  const [uploadPct, setUploadPct] = useState(0)
  const [toast, setToast] = useState(null)
  const xhrRef = useRef(null)

  // Notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  // Prevent accidental close during upload
  useEffect(() => {
    const handler = (e) => {
      if (uploading) { e.preventDefault(); e.returnValue = '' }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [uploading])

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type, id: Date.now() })
  }, [])

  // ---- File ingestion ----
  const ingestFiles = useCallback((rawFiles) => {
    const processed = rawFiles.map(f => ({
      file: f,
      name: f.name,
      path: f.webkitRelativePath || f.name,
      size: f.size,
    }))
    setItems(prev => {
      const existing = new Set(prev.map(x => x.path + x.size))
      return [...prev, ...processed.filter(f => !existing.has(f.path + f.size))]
    })
  }, [])

  const handleDrop = useCallback(async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const collected = []
    const readEntry = async (entry, basePath = '') => {
      if (entry.isFile) {
        await new Promise(res => entry.file(f => {
          f._path = basePath ? `${basePath}/${f.name}` : f.name
          collected.push(f)
          res()
        }))
      } else if (entry.isDirectory) {
        const reader = entry.createReader()
        await new Promise(res => {
          const read = () => reader.readEntries(async entries => {
            if (!entries.length) return res()
            await Promise.all(entries.map(en => readEntry(en, basePath ? `${basePath}/${entry.name}` : entry.name)))
            read()
          })
          read()
        })
      }
    }
    if (e.dataTransfer.items) {
      await Promise.all(Array.from(e.dataTransfer.items).map(item => {
        const entry = item.webkitGetAsEntry?.()
        return entry ? readEntry(entry) : null
      }))
    } else {
      collected.push(...Array.from(e.dataTransfer.files))
    }
    ingestFiles(collected)
  }, [ingestFiles])

  const handleClick = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.onchange = e => ingestFiles(Array.from(e.target.files))
    input.click()
  }

  const removeItem = (idx) => setItems(prev => prev.filter((_, i) => i !== idx))

  // ---- Upload ----
  const handleUpload = async () => {
    if (!items.length) return showToast('Sélectionnez au moins un fichier.', 'warning')
    if (!recipientEmail) return showToast('Email destinataire requis.', 'warning')
    if (!senderEmail) return showToast('Votre email est requis.', 'warning')

    const fd = new FormData()
    fd.append('email', recipientEmail)
    fd.append('sender_email', senderEmail)
    fd.append('expiration_days', expirationDays)
    fd.append('files_list', JSON.stringify(items.map(i => ({ name: i.path, size: i.size }))))
    items.forEach(i => {
      fd.append('files[]', i.file)
      fd.append('paths[]', i.path)
    })

    setUploading(true)
    setPhase('uploading')
    setUploadPct(0)

    const xhr = new XMLHttpRequest()
    xhrRef.current = xhr
    xhr.open('POST', `${backendUrl}/upload`, true)
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('authToken') || ''}`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setUploadPct(Math.round(e.loaded * 100 / e.total))
    }

    xhr.onload = () => {
      setUploading(false)
      setPhase('done')
      if (xhr.status === 200) {
        const res = JSON.parse(xhr.responseText)
        if (res.warning) {
          showToast('Fichiers envoyés, mais les emails de notification ont échoué.', 'warning')
        } else {
          showToast('Transfert effectué ! Les notifications ont été envoyées.', 'success')
        }
        setItems([])
        setRecipientEmail('')
        setSenderEmail('')
        setUploadPct(0)
        setPhase('')
      } else {
        let msg = 'Erreur lors du transfert.'
        try { msg = JSON.parse(xhr.responseText).error || msg } catch {}
        showToast(msg, 'error')
      }
    }

    xhr.onerror = () => {
      setUploading(false)
      setPhase('')
      showToast('Erreur réseau. Vérifiez votre connexion.', 'error')
    }

    xhr.send(fd)
  }

  const cancelUpload = () => {
    xhrRef.current?.abort()
    setUploading(false)
    setPhase('')
    setUploadPct(0)
  }

  const totalSize = items.reduce((acc, i) => acc + i.size, 0)

  return (
    <div className="page">
      <div className="container glow-accent">
        {/* Header */}
        <header className="app-header">
          <img src={banner} alt="iTransfer" className="app-logo" />
          <div className="flex gap-2">
            <button className="btn btn--ghost btn--sm" onClick={() => navigate('/admin')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 10-16 0"/>
              </svg>
              Admin
            </button>
          </div>
        </header>

        {/* Toast */}
        {toast && (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Main card */}
        <div className="card mb-6">
          <div className="card__body flex-col gap-6">

            {/* Emails */}
            <div className="flex gap-4" style={{ flexWrap: 'wrap' }}>
              <div className="field" style={{ flex: 1, minWidth: '200px' }}>
                <label className="field__label">Email destinataire</label>
                <input
                  className="input"
                  type="email"
                  placeholder="destinataire@exemple.com"
                  value={recipientEmail}
                  onChange={e => setRecipientEmail(e.target.value)}
                  disabled={uploading}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: '200px' }}>
                <label className="field__label">Votre email</label>
                <input
                  className="input"
                  type="email"
                  placeholder="vous@exemple.com"
                  value={senderEmail}
                  onChange={e => setSenderEmail(e.target.value)}
                  disabled={uploading}
                />
              </div>
            </div>

            {/* Expiration */}
            <div className="field">
              <label className="field__label">Expiration du lien</label>
              <select
                className="input"
                value={expirationDays}
                onChange={e => setExpirationDays(parseInt(e.target.value))}
                disabled={uploading}
              >
                <option value="3">3 jours</option>
                <option value="5">5 jours</option>
                <option value="7">7 jours</option>
                <option value="10">10 jours</option>
              </select>
            </div>

            {/* Drop zone */}
            <div
              className={`drop-zone${dragActive ? ' drop-zone--active' : ''}`}
              onDragEnter={e => { e.preventDefault(); setDragActive(true) }}
              onDragLeave={e => { e.preventDefault(); setDragActive(false) }}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
              onClick={!uploading ? handleClick : undefined}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && !uploading && handleClick()}
              aria-label="Zone de dépôt de fichiers"
            >
              <svg className="drop-zone__icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 8v24M14 18l10-10 10 10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M8 36h32" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
              <p className="drop-zone__title">Glissez vos fichiers ici</p>
              <p className="drop-zone__sub">ou cliquez pour sélectionner</p>
            </div>

            {/* File list */}
            {items.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="section-title" style={{ margin: 0 }}>
                    {items.length} fichier{items.length > 1 ? 's' : ''} — {formatSize(totalSize)}
                  </p>
                  <button className="btn btn--ghost btn--sm" onClick={() => setItems([])} disabled={uploading}>
                    Tout effacer
                  </button>
                </div>
                <div className="file-list">
                  {items.map((item, idx) => (
                    <div key={idx} className="file-item">
                      <span className="file-item__name" title={item.path}>{item.path}</span>
                      <span className="file-item__size">{formatSize(item.size)}</span>
                      <button className="file-item__remove" onClick={() => removeItem(idx)} disabled={uploading} aria-label="Supprimer">✕</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Progress */}
            {uploading && (
              <div className="progress-wrap">
                <div className="progress-label">
                  <span className="progress-label__text">
                    {phase === 'uploading' ? 'Envoi en cours…' : 'Traitement…'}
                  </span>
                  <span className="progress-label__pct">{uploadPct}%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-bar" style={{ width: `${uploadPct}%` }} />
                </div>
                <div className="toast toast--info" style={{ marginTop: 0 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0, marginTop: 2 }}>
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                  </svg>
                  <span>Ne fermez pas cette fenêtre pendant le transfert.</span>
                  <button className="btn btn--danger btn--sm" onClick={cancelUpload}>Annuler</button>
                </div>
              </div>
            )}

            {/* Send button */}
            <button
              className="btn btn--primary btn--full btn--lg"
              onClick={handleUpload}
              disabled={uploading || !items.length}
            >
              {uploading
                ? <><span className="spinner" />Envoi en cours…</>
                : <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
                    </svg>
                    Envoyer
                  </>
              }
            </button>

          </div>
        </div>

        <p className="text-center text-xs text-faint">
          iTransfer · open-source · GPL-3.0
        </p>
      </div>
    </div>
  )
}

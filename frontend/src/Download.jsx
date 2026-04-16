import { useState, useEffect } from 'react'
import banner from './assets/banner.png'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function Download() {
  const transferId = window.location.pathname.split('/').pop()
  const [files, setFiles] = useState([])
  const [expiresAt, setExpiresAt] = useState(null)
  const [senderEmail, setSenderEmail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    fetch(`${backendUrl}/transfer/${transferId}`)
      .then(r => {
        if (!r.ok) throw new Error(r.status === 410 ? 'Ce lien a expiré.' : 'Lien invalide ou introuvable.')
        return r.json()
      })
      .then(data => { setFiles(data.files || []); setExpiresAt(data.expires_at); setSenderEmail(data.sender_email); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [transferId])

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const r = await fetch(`${backendUrl}/download/${transferId}`)
      if (!r.ok) throw new Error('Erreur lors du téléchargement.')
      const blob = await r.blob()
      const cd = r.headers.get('Content-Disposition') || ''
      const match = cd.match(/filename="?([^"]+)"?/)
      const filename = match ? match[1] : `iTransfer_${transferId.slice(0, 8)}`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = filename
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setDone(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setDownloading(false)
    }
  }

  const totalSize = files.reduce((acc, f) => acc + (f.size || 0), 0)

  if (loading) return (
    <div className="page page--centered">
      <span className="spinner spinner--lg" />
    </div>
  )

  return (
    <div className="page">
      <div className="container--narrow">

        <div className="text-center mb-8">
          <img src={banner} alt="iTransfer" className="app-logo" style={{ margin: '0 auto' }} />
        </div>

        {error ? (
          <div className="toast toast--error">{error}</div>
        ) : (
          <div className="card">
            <div className="card__body flex-col gap-5">

              <div className="flex-col gap-2">
                {senderEmail && (
                  <div className="meta-row">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                      <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/><path d="M22 6l-10 7L2 6"/>
                    </svg>
                    <span>Envoyé par <strong>{senderEmail}</strong></span>
                  </div>
                )}
                {expiresAt && (
                  <div className="meta-row">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    <span>Expire le {formatDate(expiresAt)}</span>
                  </div>
                )}
              </div>

              <div className="divider" style={{ margin: 0 }} />

              <div>
                <p className="section-title">
                  {files.length} fichier{files.length > 1 ? 's' : ''} — {formatSize(totalSize)}
                </p>
                <div className="file-list">
                  {files.map((f, i) => (
                    <div key={i} className="file-item">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0, opacity: 0.5 }}>
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                      </svg>
                      <span className="file-item__name" title={f.name}>{f.name}</span>
                      <span className="file-item__size">{formatSize(f.size)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {done && (
                <div className="toast toast--success">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0 }}>
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                  </svg>
                  Téléchargement lancé. Vérifiez votre dossier de téléchargements.
                </div>
              )}

              <button className="btn btn--primary btn--full btn--lg" onClick={handleDownload} disabled={downloading}>
                {downloading
                  ? <><span className="spinner" />Préparation…</>
                  : <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>Télécharger {files.length > 1 ? 'les fichiers' : 'le fichier'}</>
                }
              </button>

            </div>
          </div>
        )}

        <div className="page-footer">
          <p>iTransfer est un logiciel libre distribué sous licence GPL-3.0.</p>
          <a href="https://github.com/tiritibambix/iTransfer/" target="_blank" rel="noopener noreferrer" className="footer-link">
            <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor">
              <path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            Voir sur GitHub
          </a>
        </div>

      </div>
    </div>
  )
}
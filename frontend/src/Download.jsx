import { useState, useEffect } from 'react'
import { useT } from './i18n'
import Header from './Header'
import Footer from './Footer'

const backendUrl = window.BACKEND_URL

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

function formatDate(iso, locale) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(locale, {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function Download() {
  const transferId = window.location.pathname.split('/').pop()
  const { t, lang } = useT()
  const [files, setFiles] = useState([])
  const [expiresAt, setExpiresAt] = useState(null)
  const [senderEmail, setSenderEmail] = useState(null)
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    fetch(`${backendUrl}/transfer/${transferId}`)
      .then(r => {
        if (!r.ok) throw new Error(r.status === 410 ? 'expired' : 'invalid')
        return r.json()
      })
      .then(data => {
        setFiles(data.files || [])
        setExpiresAt(data.expires_at)
        setSenderEmail(data.sender_email)
        setMessage(data.message || null)
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [transferId])

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const r = await fetch(`${backendUrl}/download/${transferId}`)
      if (!r.ok) throw new Error('downloadFailed')
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
  const errorText = ({ expired: t('dl.linkExpired'), invalid: t('dl.invalidLink'), downloadFailed: t('dl.downloadFailed') })[error] || error

  if (loading) return (
    <div className="page page--centered">
      <span className="spinner spinner--lg" />
    </div>
  )

  return (
    <div className="page page--centered">
      <div className="container--narrow">

        <Header />

        {error ? (
          <div className="toast toast--error">{errorText}</div>
        ) : (
          <div className="card">
            <div className="card__body flex-col gap-5">

              <div className="flex-col gap-2">
                {senderEmail && (
                  <div className="meta-row">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                      <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/><path d="M22 6l-10 7L2 6"/>
                    </svg>
                    <span>{t('dl.sentBy')} <strong>{senderEmail}</strong></span>
                  </div>
                )}
                {expiresAt && (
                  <div className="meta-row">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    <span>{t('dl.expiresOn', { date: formatDate(expiresAt, lang) })}</span>
                  </div>
                )}
              </div>

              {message && (
                <div className="user-message-box">
                  <span className="user-message-box__label">{t('dl.messageLabel')}</span>
                  <p style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{message}</p>
                </div>
              )}

              <div className="divider" style={{ margin: 0 }} />

              <div>
                <p className="section-title">
                  {t(files.length === 1 ? 'files.one' : 'files.other', { count: files.length, size: formatSize(totalSize) })}
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
                  {t('dl.downloadStarted')}
                </div>
              )}

              <button className="btn btn--primary btn--full btn--lg" onClick={handleDownload} disabled={downloading}>
                {downloading
                  ? <><span className="spinner" />{t('dl.preparing')}</>
                  : <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>{t(files.length === 1 ? 'dl.downloadFile' : 'dl.downloadFiles')}</>
                }
              </button>

            </div>
          </div>
        )}

        <Footer />

      </div>
    </div>
  )
}

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import banner from './assets/iTransfer Bannière.png';

function Download() {
  const { transferId } = useParams();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const backendUrl = window.BACKEND_URL;

  useEffect(() => {
    fetchTransferDetails();
  }, [transferId]);

  const fetchTransferDetails = async () => {
    try {
      const response = await fetch(`${backendUrl}/transfer/${transferId}`);
      if (!response.ok) {
        throw new Error('Lien de téléchargement invalide ou expiré');
      }
      const data = await response.json();
      setFiles(data.files);
      setLoading(false);
    } catch (error) {
      setError(error.message);
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(`${backendUrl}/download/${transferId}`);
      if (!response.ok) throw new Error('Erreur lors du téléchargement');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = files.length > 1 ? `iTransfer_${new Date().getFullYear().toString().slice(-2)}${String(new Date().getMonth() + 1).padStart(2, '0')}${String(new Date().getDate()).padStart(2, '0')}${String(new Date().getHours()).padStart(2, '0')}${String(new Date().getMinutes()).padStart(2, '0')}.zip` : files[0].name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Erreur lors du téléchargement. Veuillez réessayer.');
    }
  };

  if (loading) {
    return (
      <div className="app-container" style={{
        padding: 'clamp(1rem, 3vw, 2rem)',
        maxWidth: '800px',
        width: '100%',
        margin: '0 auto',
        textAlign: 'center'
      }}>
        Chargement...
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-container" style={{
        padding: 'clamp(1rem, 3vw, 2rem)',
        maxWidth: '800px',
        width: '100%',
        margin: '0 auto',
        textAlign: 'center'
      }}>
        <div style={{ color: 'var(--clr-error)' }}>{error}</div>
      </div>
    );
  }

  return (
    <div className="app-container" style={{
      padding: 'clamp(1rem, 3vw, 2rem)',
      maxWidth: '800px',
      width: '100%',
      margin: '0 auto',
      boxSizing: 'border-box'
    }}>
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 'clamp(2rem, 4vw, 3rem)'
      }}>
        <img 
          src={banner}
          alt="iTransfer"
          style={{
            height: 'clamp(2rem, 6vw, 3rem)',
            width: 'auto',
            objectFit: 'contain'
          }}
        />
      </div>

      <div className="main-content" style={{
        backgroundColor: 'var(--clr-surface-a10)',
        padding: 'clamp(1rem, 3vw, 2rem)',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      }}>
        <h1 style={{
          fontSize: 'clamp(1.5rem, 3vw, 2rem)',
          textAlign: 'center',
          marginBottom: 'clamp(1.5rem, 3vw, 2rem)',
          color: 'var(--clr-primary-a50)'
        }}>
          Vos fichiers sont prêts à être téléchargés
        </h1>

        <div style={{
          backgroundColor: 'var(--clr-surface-a20)',
          padding: 'clamp(1rem, 3vw, 1.5rem)',
          borderRadius: '8px',
          marginBottom: 'clamp(1.5rem, 3vw, 2rem)'
        }}>
          <h3 style={{
            margin: '0 0 1rem 0',
            fontSize: 'clamp(1rem, 2.5vw, 1.25rem)'
          }}>
            Fichiers à télécharger :
          </h3>
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto',
            padding: '0.5rem'
          }}>
            {files.map((file, index) => (
              <div key={index} style={{
                padding: '0.8rem',
                borderBottom: index < files.length - 1 ? '1px solid var(--clr-surface-a30)' : 'none',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ fontSize: '1rem' }}>{file.name}</div>
                  <div style={{ 
                    fontSize: '0.9rem',
                    color: 'var(--clr-primary-a40)',
                    marginTop: '0.25rem'
                  }}>
                    {formatFileSize(file.size)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button 
          onClick={handleDownload}
          style={{
            width: '100%',
            padding: 'clamp(1rem, 3vw, 1.5rem)',
            fontSize: 'clamp(1rem, 3vw, 1.25rem)',
            backgroundColor: 'var(--clr-primary-a30)',
            transition: 'all 0.3s ease'
          }}
        >
          Télécharger {files.length > 1 ? 'les fichiers' : 'le fichier'}
        </button>
      </div>
    </div>
  );
}

export default Download;
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ProgressBar from './ProgressBar';

const styles = {
  uploadContainer: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: 'var(--clr-surface-a10)',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
  },
  uploadContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px'
  },
  fileInputContainer: {
    width: '100%',
    maxWidth: '400px'
  },
  fileInput: {
    display: 'none'
  },
  fileLabel: {
    display: 'block',
    padding: '12px 20px',
    backgroundColor: 'var(--clr-surface-a20)',
    color: 'var(--clr-primary-a50)',
    borderRadius: '5px',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'background-color 0.3s',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  uploadButton: {
    minWidth: '150px',
    backgroundColor: 'var(--clr-primary-a30)',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'background-color 0.3s'
  },
  uploadButtonDisabled: {
    backgroundColor: 'var(--clr-surface-a30)',
    cursor: 'not-allowed'
  },
  message: {
    padding: '10px',
    borderRadius: '5px',
    textAlign: 'center',
    width: '100%',
    maxWidth: '400px'
  },
  success: {
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
    color: '#4caf50'
  },
  error: {
    backgroundColor: 'rgba(244, 67, 54, 0.1)',
    color: '#f44336'
  },
  settingsLink: {
    display: 'inline-block',
    marginTop: '20px',
    fontSize: '12px',
    color: 'var(--clr-primary-a40)',
    textDecoration: 'none',
    opacity: 0.7,
    transition: 'opacity 0.3s'
  }
};

const Upload = ({ backendUrl }) => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage('');
    setProgress(0);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Veuillez sélectionner un fichier.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${backendUrl}/upload`, true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 201) {
          setMessage('Fichier uploadé avec succès !');
          setProgress(0);
        } else {
          setMessage('Erreur lors de l\'upload.');
        }
      };

      xhr.onerror = () => {
        setMessage('Erreur réseau lors de l\'upload.');
      };

      xhr.send(formData);
    } catch (error) {
      setMessage('Erreur réseau ou backend.');
      console.error(error);
    }
  };

  return (
    <div style={styles.uploadContainer}>
      <h1>iTransfer</h1>
      <div style={styles.uploadContent}>
        <div style={styles.fileInputContainer}>
          <input 
            type="file" 
            id="file" 
            style={styles.fileInput} 
            onChange={handleFileChange} 
          />
          <label htmlFor="file" style={styles.fileLabel}>
            {file ? file.name : 'Choisir un fichier'}
          </label>
        </div>
        
        <button 
          style={{
            ...styles.uploadButton,
            ...((!file || progress > 0) && styles.uploadButtonDisabled)
          }} 
          onClick={handleUpload} 
          disabled={!file || progress > 0}
        >
          {progress > 0 ? 'Envoi en cours...' : 'Envoyer'}
        </button>
        
        {progress > 0 && <ProgressBar progress={progress} />}
        
        {message && (
          <p style={{
            ...styles.message,
            ...(message.includes('succès') ? styles.success : styles.error)
          }}>
            {message}
          </p>
        )}
      </div>
      
      <Link to="/smtp-settings" style={styles.settingsLink}>
        Paramètres SMTP
      </Link>
    </div>
  );
};

export default Upload;

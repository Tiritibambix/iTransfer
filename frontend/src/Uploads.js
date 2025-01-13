import React, { useState } from 'react';
import ProgressBar from './ProgressBar';
import { Link } from 'react-router-dom';

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
    <div className="upload-container">
      <h1>iTransfer</h1>
      <div className="upload-content">
        <div className="file-input-container">
          <input 
            type="file" 
            id="file" 
            className="file-input" 
            onChange={handleFileChange} 
          />
          <label htmlFor="file" className="file-label">
            {file ? file.name : 'Choisir un fichier'}
          </label>
        </div>
        
        <button className="upload-button" onClick={handleUpload} disabled={!file}>
          {progress > 0 ? 'Envoi en cours...' : 'Envoyer'}
        </button>
        
        {progress > 0 && <ProgressBar progress={progress} />}
        
        {message && (
          <p className={`message ${message.includes('succès') ? 'success' : 'error'}`}>
            {message}
          </p>
        )}
      </div>
      
      <Link to="/smtp-settings" className="settings-link">
        Paramètres SMTP
      </Link>

      <style jsx>{`
        .upload-container {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
          background-color: var(--clr-surface-a10);
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .upload-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }

        .file-input-container {
          width: 100%;
          max-width: 400px;
        }

        .file-input {
          display: none;
        }

        .file-label {
          display: block;
          padding: 12px 20px;
          background-color: var(--clr-surface-a20);
          color: var(--clr-primary-a50);
          border-radius: 5px;
          cursor: pointer;
          text-align: center;
          transition: background-color 0.3s;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .file-label:hover {
          background-color: var(--clr-surface-a30);
        }

        .upload-button {
          min-width: 150px;
          background-color: var(--clr-primary-a30);
          color: white;
        }

        .upload-button:hover:not(:disabled) {
          background-color: var(--clr-primary-a40);
        }

        .upload-button:disabled {
          background-color: var(--clr-surface-a30);
          cursor: not-allowed;
        }

        .message {
          padding: 10px;
          border-radius: 5px;
          text-align: center;
          width: 100%;
          max-width: 400px;
        }

        .success {
          background-color: rgba(76, 175, 80, 0.1);
          color: #4caf50;
        }

        .error {
          background-color: rgba(244, 67, 54, 0.1);
          color: #f44336;
        }

        .settings-link {
          display: inline-block;
          margin-top: 20px;
          font-size: 12px;
          color: var(--clr-primary-a40);
          text-decoration: none;
          opacity: 0.7;
          transition: opacity 0.3s;
        }

        .settings-link:hover {
          opacity: 1;
        }
      `}</style>
    </div>
  );
};

export default Upload;

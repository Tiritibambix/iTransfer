import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ProgressBar from './ProgressBar';
import './Uploads.css';

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
    </div>
  );
};

export default Upload;

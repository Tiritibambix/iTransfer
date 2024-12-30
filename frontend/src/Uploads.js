import React, { useState } from 'react';
import ProgressBar from './ProgressBar';

function Upload() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState('');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file || !email) {
      setMessage('Veuillez fournir un fichier et une adresse email.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', email);

    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', 'http://localhost:4500/upload', true);

      // Gestion de la progression
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setProgress(percentComplete);
        }
      };

      // Gestion de la réponse
      xhr.onload = () => {
        if (xhr.status === 201) {
          setMessage('Fichier uploadé avec succès !');
          setProgress(0);
        } else {
          setMessage('Erreur lors de l\'upload.');
        }
      };

      // Gestion des erreurs réseau
      xhr.onerror = () => {
        setMessage('Erreur réseau lors de l\'upload.');
      };

      xhr.send(formData);
    } catch (error) {
      console.error('Erreur réseau ou backend :', error);
      setMessage('Erreur inconnue. Vérifiez la console pour plus d\'informations.');
    }
  };

  return (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <h1>Upload File</h1>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Votre email"
        style={{ display: 'block', margin: '10px auto', padding: '10px', width: '300px' }}
      />
      <input
        type="file"
        onChange={handleFileChange}
        style={{ display: 'block', margin: '10px auto', padding: '10px' }}
      />
      <button
        onClick={handleUpload}
        style={{
          display: 'block',
          margin: '10px auto',
          padding: '10px 20px',
          backgroundColor: '#4caf50',
          color: '#fff',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
        }}
      >
        Upload
      </button>
      {progress > 0 && <ProgressBar progress={progress} />}
      {message && <p>{message}</p>}
    </div>
  );
}

export default Upload;

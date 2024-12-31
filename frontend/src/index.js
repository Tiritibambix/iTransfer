import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import './index.css'; // Chemin relatif correct

// URL dynamique du backend via variables d'environnement ou fallback
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

const App = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Veuillez sélectionner un fichier.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'upload');
      }

      const data = await response.json();
      setMessage(data.message || 'Fichier uploadé avec succès.');
    } catch (error) {
      setMessage('Erreur lors de l\'upload. Vérifiez le backend.');
      console.error(error);
    }
  };

  return (
    <div>
      <h1>iTransfer</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {message && <p>{message}</p>}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));

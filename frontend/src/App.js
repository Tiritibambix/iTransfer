import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [email, setEmail] = useState('');
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !file) {
      setMessage('Veuillez saisir un email et sélectionner un fichier.');
      return;
    }

    const formData = new FormData();
    formData.append('email', email);
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        },
      });
      setMessage(response.data.message);
    } catch (error) {
      setMessage('Erreur lors de l’envoi du fichier.');
      console.error(error);
    }
  };

  return (
    <div className="App">
      <h1>Uploader un fichier</h1>
      <form onSubmit={handleSubmit} className="upload-form">
        <label>
          Email du destinataire :
          <input
            type="email"
            value={email}
            onChange={handleEmailChange}
            placeholder="Entrez l'email du destinataire"
            required
          />
        </label>
        <label>
          Sélectionner un fichier :
          <input type="file" onChange={handleFileChange} required />
        </label>
        <button type="submit">Envoyer</button>
      </form>
      {progress > 0 && <progress value={progress} max="100">{progress}%</progress>}
      {message && <p>{message}</p>}
    </div>
  );
}

export default App;

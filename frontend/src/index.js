import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';

// Récupérer l'URL du backend depuis les variables d'environnement
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

console.log('Backend URL configurée :', backendUrl);

ReactDOM.render(
  <React.StrictMode>
    <App backendUrl={backendUrl} />
  </React.StrictMode>,
  document.getElementById('root')
);

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

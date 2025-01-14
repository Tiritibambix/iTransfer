import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';

function App({ backendUrl }) {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const xhrRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setProgress(0);
  };

  const handleUpload = () => {
    if (!selectedFile || !recipientEmail) {
      alert('Veuillez sélectionner un fichier et saisir un email');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('email', recipientEmail);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${backendUrl}/upload`, true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 201) {
        const response = JSON.parse(xhr.responseText);
        if (response.email_sent) {
          alert('Le fichier a été uploadé et un email a été envoyé au destinataire.');
        } else {
          alert('Le fichier a été uploadé mais l\'envoi de l\'email a échoué.');
        }
      } else {
        alert('Erreur lors de l\'upload. Veuillez vérifier que l\'email est valide et réessayer.');
      }
      setProgress(0);
      setSelectedFile(null);
      setRecipientEmail('');
    };

    xhr.onerror = () => {
      alert('Erreur réseau lors de l\'upload');
      setProgress(0);
    };

    xhr.send(formData);
    xhrRef.current = xhr;
  };

  return (
    <div className="container">
      <h1>iTransfer</h1>

      <div>
        <input
          type="email"
          className="input"
          placeholder="Email du destinataire"
          value={recipientEmail}
          onChange={(e) => setRecipientEmail(e.target.value)}
        />

        <input
          type="file"
          id="file"
          onChange={handleFileChange}
          className="input"
          style={{ display: 'none' }}
        />
        <label htmlFor="file" className="button-secondary">
          {selectedFile ? selectedFile.name : 'Choisir un fichier'}
        </label>

        {progress > 0 && (
          <div className="message-info">
            Envoi en cours : {progress}%
          </div>
        )}

        <button
          className="button"
          onClick={handleUpload}
          disabled={!selectedFile || !recipientEmail || progress > 0}
        >
          Envoyer
        </button>
      </div>

      <Link to="/smtp-settings" className="button-secondary" style={{ marginTop: '20px' }}>
        Paramètres SMTP
      </Link>
    </div>
  );
}

export default App;

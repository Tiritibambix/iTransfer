import React, { useState, useRef } from 'react';
import SMTPSettings from './SMTPSettings';

function App({ backendUrl }) {
  console.log('backendUrl:', backendUrl); // Debug: Vérification de l'URL backend

  const [progress, setProgress] = useState(0); // État pour la progression
  const [recipientEmail, setRecipientEmail] = useState(''); // État pour l'email du destinataire
  const xhrRef = useRef(null); // Référence pour stocker l'objet XMLHttpRequest

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    console.log('Fichier à envoyer :', file); // Debug: Log du fichier sélectionné

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${backendUrl}/upload`, true);

    // Mise à jour de la barre de progression
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setProgress(percent);
      }
    };

    // Gérer la réponse du serveur
    xhr.onload = () => {
      console.log('Réponse backend :', xhr.responseText); // Debug: Log de la réponse
      if (xhr.status === 201) {
        console.log('Upload réussi');
      } else {
        console.error('Erreur lors de l\'upload :', xhr.status, xhr.statusText);
      }
      setProgress(0); // Réinitialiser la progression après l'upload
    };

    // Gérer les erreurs
    xhr.onerror = () => {
      console.error('Erreur réseau lors de l\'upload');
      setProgress(0);
    };

    xhr.setRequestHeader('Accept', 'application/json'); // Assurez la compatibilité CORS
    xhr.send(formData); // Envoyer la requête avec le fichier
  };

  // Fonction pour annuler l'upload
  const cancelUpload = () => {
    if (xhrRef.current) {
      xhrRef.current.abort(); // Annule l'envoi
      console.log('Upload annulé');
      setProgress(0); // Réinitialise la progression
    }
  };

  // Fonction pour mettre à jour l'email du destinataire
  const handleRecipientEmailChange = (event) => {
    setRecipientEmail(event.target.value);
  };

  const handleUpload = () => {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput.files.length > 0) {
      handleFileUpload({ target: fileInput });
    }
  };

  return (
    <div>
      <SMTPSettings backendUrl={backendUrl} />
      <button className="btn" style={{ float: 'right' }} onClick={() => window.location.href = '/smtp-settings'}>Paramètres</button>
      <h1>iTransfer</h1>
      <input type="email" className="btn" value={recipientEmail} onChange={handleRecipientEmailChange} placeholder="Email du destinataire" />
      <input type="file" className="btn" />
      <button className="btn" onClick={handleUpload}>Upload</button>

      {/* Affichage de la barre de progression */}
      {progress > 0 && (
        <div style={{ width: '100%', backgroundColor: '#ccc', height: '10px' }}>
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: 'green',
            }}
          />
        </div>
      )}

      {/* Bouton "Annuler l'envoi" */}
      {progress > 0 && (
        <button
          onClick={cancelUpload}
          style={{ marginTop: '10px', backgroundColor: 'red', color: 'white' }}
        >
          Annuler l'envoi
        </button>
      )}
    </div>
  );
}

export default App;

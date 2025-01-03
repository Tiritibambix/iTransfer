import React, { useState, useRef } from 'react';

function App({ backendUrl }) {
  console.log('backendUrl:', backendUrl); // Ajoutez ce log

  const [progress, setProgress] = useState(0); // État pour la progression
  const xhrRef = useRef(null); // Référence pour stocker l'objet XMLHttpRequest

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    console.log('Fichier à envoyer :', file); // Log ajouté pour le debug

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${backendUrl}/upload`, true);

    // Sauvegarde de la requête pour pouvoir l'annuler
    xhrRef.current = xhr;

    // Mise à jour de la barre de progression
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setProgress(percent);
      }
    };

    // Gérer la réponse du serveur
    xhr.onload = () => {
      console.log('Réponse backend :', xhr.responseText); // Log ajouté pour le debug
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
      setProgress(0); // Réinitialiser la progression en cas d'erreur
    };

    // Envoyer la requête avec les données
    xhr.setRequestHeader('Accept', 'application/json'); // Assurez la compatibilité CORS
    xhr.send(formData);
  };

  // Fonction pour annuler l'upload
  const cancelUpload = () => {
    if (xhrRef.current) {
      xhrRef.current.abort(); // Annule l'envoi
      console.log('Upload annulé');
      setProgress(0); // Réinitialise la progression
    }
  };

  return (
    <div>
      <h1>Application iTransfer</h1>
      <input type="file" onChange={handleFileUpload} />

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

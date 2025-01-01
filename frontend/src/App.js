import React, { useState } from 'react';

function App({ backendUrl }) {
  const [progress, setProgress] = useState(0);  // État pour la progression

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

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
      if (xhr.status === 201) {
        console.log('Fichier téléchargé avec succès:', xhr.responseText);
      } else {
        console.error('Erreur lors de l\'upload:', xhr.status, xhr.statusText);
      }
      setProgress(0);  // Réinitialiser la progression après l'upload
    };

    // Gérer les erreurs
    xhr.onerror = () => {
      console.error('Erreur lors de l\'upload du fichier');
      setProgress(0);  // Réinitialiser la progression en cas d'erreur
    };

    // Envoyer la requête avec les données
    xhr.send(formData);
  };

  return (
    <div>
      <h1>Upload de fichier</h1>
      <input type="file" onChange={handleFileUpload} />
      
      {/* Affichage de la barre de progression */}
      {progress > 0 && (
        <div style={{ width: '100%', backgroundColor: '#ccc', height: '10px' }}>
          <div style={{
            width: `${progress}%`,
            height: '100%',
            backgroundColor: 'green'
          }} />
        </div>
      )}
    </div>
  );
}

export default App;

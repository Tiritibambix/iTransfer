import React, { useState } from 'react';

function App() {
  const [uploading, setUploading] = useState(false);

  // Récupérer dynamiquement l'URL du backend à partir de l'environnement
  const backendUrl = window.location.origin.replace('3500', '5500');  // Dynamique : on change le port 3500 -> 5500

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);  // Démarrer l'upload

    try {
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      setUploading(false);  // Fin de l'upload

      if (!response.ok) {
        throw new Error(`Erreur: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Réponse du backend:', data);
    } catch (error) {
      setUploading(false);
      console.error('Erreur lors de l\'envoi du fichier:', error);
    }
  };

  return (
    <div>
      <h1>Upload de fichier</h1>
      <input type="file" onChange={handleFileUpload} />
      {uploading && <button disabled>Upload en cours...</button>}
      {!uploading && <button onClick={handleFileUpload}>Upload</button>}
    </div>
  );
}

export default App;

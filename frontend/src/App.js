import React, { useState } from 'react';

function App() {
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState(null); // Suivi du fichier sélectionné

  // Récupérer dynamiquement l'URL du backend
  const backendUrl = window.location.origin.replace('3500', '5500');  // Dynamique : on change le port 3500 -> 5500

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    } else {
      setFile(null); // Aucun fichier sélectionné
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);

    try {
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      setUploading(false);

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
      <input type="file" onChange={handleFileChange} />
      {file && !uploading && (
        <button onClick={handleFileUpload}>Upload</button>
      )}
      {uploading && <button disabled>Upload en cours...</button>}
    </div>
  );
}

export default App;

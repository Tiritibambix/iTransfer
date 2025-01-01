import React, { useState } from 'react';

function App({ backendUrl }) {
  const [file, setFile] = useState(null);  // État pour gérer le fichier sélectionné
  const [progress, setProgress] = useState(0); // État pour la progression

  // Gérer la sélection de fichier
  const handleFileChange = (event) => {
    setFile(event.target.files[0]);  // Sauvegarder le fichier sélectionné
  };

  // Gérer l'upload du fichier
  const handleFileUpload = async () => {
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          // Ne pas spécifier le Content-Type ici, fetch le gère automatiquement pour FormData
        },
      });

      if (!response.ok) {
        throw new Error(`Erreur: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Réponse du backend:', data);
    } catch (error) {
      console.error('Erreur lors de l\'envoi du fichier:', error);
    }
  };

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Upload de fichier</h1>
      <input
        type="file"
        onChange={handleFileChange}
        style={{
          padding: '10px',
          fontSize: '16px',
          marginTop: '20px',
          cursor: 'pointer',
        }}
      />
      
      {/* Affichage du bouton "Upload" si un fichier a été sélectionné */}
      {file && (
        <button
          onClick={handleFileUpload}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            marginTop: '20px',
            cursor: 'pointer',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
          }}
        >
          Upload
        </button>
      )}

      {/* Affichage de la barre de progression */}
      <div style={{ marginTop: '20px' }}>
        {progress > 0 && (
          <div>
            <progress value={progress} max="100" />
            <span>{progress}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

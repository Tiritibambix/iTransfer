import React from 'react';

function App({ backendUrl }) {
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
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
        onChange={handleFileUpload}
        style={{
          padding: '10px',
          fontSize: '16px',
          marginTop: '20px',
          cursor: 'pointer',
        }}
      />
    </div>
  );
}

export default App;

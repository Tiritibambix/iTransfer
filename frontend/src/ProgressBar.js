import React, { useState } from 'react';

function Uploads({ onFileUpload }) {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUploadClick = () => {
    if (file) {
      onFileUpload(file);  // Appelle la fonction d'upload avec le fichier sélectionné
    }
  };

  return (
    <div className="upload">
      <h2>Upload de fichier</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUploadClick}>Upload</button>
    </div>
  );
}

export default Uploads;

import React, { useState } from 'react';

const FileManager = ({ onError }) => {
  const [files, setFiles] = useState([]);

  const handleFileUpload = (event) => {
    const uploadedFiles = Array.from(event.target.files);
    if (uploadedFiles.length === 0) {
      onError('Aucun fichier sélectionné.');
      return;
    }
    setFiles(uploadedFiles);
  };

  return (
    <div>
      <h1>Gestionnaire de fichiers</h1>
      <input type="file" multiple onChange={handleFileUpload} />
      <ul>
        {files.map((file, index) => (
          <li key={index}>{file.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default FileManager;

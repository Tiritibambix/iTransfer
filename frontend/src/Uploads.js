import React, { useState } from 'react';
import ProgressBar from './ProgressBar';

function Upload() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (!file || !email) {
      alert('Veuillez fournir un fichier et une adresse email.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', email);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://localhost:5000/upload', true);

    // Suivi de la progression
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        setProgress(percentComplete);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 201) {
        alert('Fichier uploadé avec succès!');
        setProgress(0);
      } else {
        alert('Erreur lors de l\'upload');
      }
    };

    xhr.onerror = () => alert('Une erreur réseau s\'est produite.');
    xhr.send(formData);
  };

  return (
    <div>
      <h1>Upload File</h1>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Votre email"
      />
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {progress > 0 && <ProgressBar progress={progress} />}
    </div>
  );
}

export default Upload;

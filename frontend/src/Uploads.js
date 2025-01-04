import React, { useState } from 'react';
import ProgressBar from './ProgressBar';

const Upload = ({ backendUrl }) => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleRecipientEmailChange = (e) => {
    setRecipientEmail(e.target.value);
  };

  const handleUpload = async () => {
    if (!file || !recipientEmail) {
      setMessage('Veuillez sélectionner un fichier et entrer un email destinataire.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', recipientEmail);

    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${backendUrl}/upload`, true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 201) {
          setMessage('Fichier uploadé avec succès !');
          setProgress(0);
        } else {
          setMessage('Erreur lors de l\'upload.');
        }
      };

      xhr.onerror = () => {
        setMessage('Erreur réseau lors de l\'upload.');
      };

      xhr.send(formData);
    } catch (error) {
      setMessage('Erreur réseau ou backend.');
      console.error(error);
    }
  };

  return (
    <div>
      <h1>iTransfer</h1>
      <input type="file" onChange={handleFileChange} />
      <input type="email" value={recipientEmail} onChange={handleRecipientEmailChange} placeholder="Email du destinataire" />
      <button onClick={handleUpload}>Upload</button>
      {progress > 0 && <ProgressBar progress={progress} />}
      {message && <p>{message}</p>}
    </div>
  );
};

export default Upload;

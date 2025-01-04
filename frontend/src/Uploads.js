import React, { useState } from 'react';
import ProgressBar from './ProgressBar';

const Upload = ({ backendUrl }) => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [recipientEmail2, setRecipientEmail2] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleRecipientEmailChange = (e) => {
    setRecipientEmail(e.target.value);
  };

  const handleSenderEmailChange = (e) => {
    setSenderEmail(e.target.value);
  };

  const handleRecipientEmail2Change = (e) => {
    setRecipientEmail2(e.target.value);
  };

  const handleUpload = async () => {
    if (!file || !recipientEmail || !senderEmail) {
      setMessage('Veuillez sélectionner un fichier et entrer un email destinataire et expéditeur.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', recipientEmail);
    formData.append('senderEmail', senderEmail);

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
      <input type="file" className="btn" onChange={handleFileChange} />
      <input type="email" className="btn" value={senderEmail} onChange={handleSenderEmailChange} placeholder="Email de l'expéditeur" />
      <input type="email" className="btn" value={recipientEmail} onChange={handleRecipientEmailChange} placeholder="Email du destinataire" />
      <input type="email" className="btn" value={recipientEmail2} onChange={handleRecipientEmail2Change} placeholder="Email du destinataire 2" />
      <button className="btn" onClick={handleUpload}>Upload</button>
      <button className="btn" onClick={() => window.location.href = '/smtp-settings'}>Configuration SMTP</button>
      <button className="btn" onClick={() => window.location.href = '/smtp-settings'}>Configuration SMTP</button>
      {progress > 0 && <ProgressBar progress={progress} />}
      {message && <p>{message}</p>}
    </div>
  );
};

export default Upload;

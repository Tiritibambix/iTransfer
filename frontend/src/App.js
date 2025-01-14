import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function App({ backendUrl }) {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const xhrRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      console.error('Aucun fichier sélectionné');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', recipientEmail);
    formData.append('senderEmail', senderEmail);

    console.log('Fichier à envoyer :', file);
    console.log('Email du destinataire :', recipientEmail);
    console.log('Email de l\'expéditeur :', senderEmail);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${backendUrl}/upload`, true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 201) {
        const response = JSON.parse(xhr.responseText);
        console.log('Upload réussi');
        if (response.email_sent) {
          alert('Le fichier a été uploadé et un email a été envoyé au destinataire.');
        } else {
          alert('Le fichier a été uploadé mais l\'envoi de l\'email a échoué.');
        }
      } else {
        console.error('Erreur lors de l\'upload :', xhr.status, xhr.statusText);
        alert('Erreur lors de l\'upload. Veuillez vérifier que l\'email est valide et réessayer.');
      }
      setProgress(0);
    };

    xhr.onerror = () => {
      console.error('Erreur réseau lors de l\'upload');
      alert('Erreur réseau lors de l\'upload. Veuillez vérifier votre connexion et réessayer.');
      setProgress(0);
    };

    xhr.setRequestHeader('Accept', 'application/json');
    xhr.send(formData);
  };

  const cancelUpload = () => {
    if (xhrRef.current) {
      xhrRef.current.abort();
      console.log('Upload annulé');
      setProgress(0);
    }
  };

  const handleRecipientEmailChange = (event) => {
    setRecipientEmail(event.target.value);
  };

  const handleSenderEmailChange = (event) => {
    setSenderEmail(event.target.value);
  };

  const handleUpload = () => {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput.files.length > 0) {
      handleFileUpload({ target: fileInput });
    }
  };

  return (
    <div>
      <button className="btn" style={{ float: 'right' }} onClick={() => navigate('/smtp-settings')}>Paramètres</button>
      <h1>iTransfer</h1>
      <input type="email" className="btn" value={senderEmail} onChange={handleSenderEmailChange} placeholder="Email de l'expéditeur" />
      <input type="email" className="btn" value={recipientEmail} onChange={handleRecipientEmailChange} placeholder="Email du destinataire" />
      <input type="file" className="btn" />
      <button className="btn" onClick={handleUpload}>Upload</button>

      {progress > 0 && (
        <div style={{ width: '100%', backgroundColor: '#ccc', height: '10px' }}>
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: 'green',
            }}
          />
        </div>
      )}

      {progress > 0 && (
        <button onClick={cancelUpload}>Annuler l'envoi</button>
      )}
    </div>
  );
}

export default App;

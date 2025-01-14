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

    if (!recipientEmail || !senderEmail) {
      alert('Veuillez remplir les adresses email du destinataire et de l\'expéditeur');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', recipientEmail);
    formData.append('sender_email', senderEmail);

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
      if (xhr.status === 201 || xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        console.log('Upload réussi');
        if (response.warning) {
          alert('Le fichier a été uploadé mais il y a eu un problème avec l\'envoi des notifications.');
        } else {
          alert('Le fichier a été uploadé et les notifications ont été envoyées.');
        }
      } else {
        console.error('Erreur lors de l\'upload :', xhr.status, xhr.statusText);
        alert('Erreur lors de l\'upload. Veuillez vérifier que les emails sont valides et réessayer.');
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
    xhrRef.current = xhr;
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
    } else {
      alert('Veuillez sélectionner un fichier');
    }
  };

  return (
    <div>
      <button className="btn" style={{ float: 'right' }} onClick={() => navigate('/smtp-settings')}>Paramètres</button>
      <h1>iTransfer</h1>
      <div style={{ marginBottom: '10px' }}>
        <input 
          type="email" 
          className="btn" 
          value={senderEmail} 
          onChange={handleSenderEmailChange} 
          placeholder="Votre email (expéditeur)" 
          style={{ marginBottom: '5px', width: '100%' }}
        />
        <input 
          type="email" 
          className="btn" 
          value={recipientEmail} 
          onChange={handleRecipientEmailChange} 
          placeholder="Email du destinataire" 
          style={{ width: '100%' }}
        />
      </div>
      <div style={{ marginBottom: '10px' }}>
        <input type="file" className="btn" style={{ marginRight: '10px' }} />
        <button className="btn" onClick={handleUpload}>Upload</button>
      </div>

      {progress > 0 && (
        <div>
          <div style={{ width: '100%', backgroundColor: '#ccc', height: '10px', marginBottom: '10px' }}>
            <div
              style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: 'green',
              }}
            />
          </div>
          <button onClick={cancelUpload} className="btn">Annuler l'envoi</button>
        </div>
      )}
    </div>
  );
}

export default App;

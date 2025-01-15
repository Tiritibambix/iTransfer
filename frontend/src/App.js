import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function App() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const xhrRef = useRef(null);
  const fileInputRef = useRef(null);
  const backendUrl = window.BACKEND_URL;

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

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload({ target: { files: [e.dataTransfer.files[0]] } });
    }
  };

  return (
    <div className="app-container" style={{
      padding: '2rem',
      maxWidth: '800px',
      width: '100%',
      margin: '0 auto'
    }}>
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          margin: 0,
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>iTransfer</h1>
        <button 
          onClick={() => navigate('/smtp-settings')}
          style={{
            backgroundColor: 'var(--clr-surface-a20)',
            color: 'var(--clr-primary-a50)',
            transition: 'all 0.3s ease'
          }}
        >
          Paramètres
        </button>
      </div>

      <div className="main-content" style={{
        backgroundColor: 'var(--clr-surface-a10)',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      }}>
        <div className="email-inputs" style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '2rem'
        }}>
          <input 
            type="email" 
            placeholder="Email du destinataire"
            value={recipientEmail}
            onChange={handleRecipientEmailChange}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-primary-a50)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '6px',
              fontSize: '1rem'
            }}
          />
          <input 
            type="email"
            placeholder="Votre email"
            value={senderEmail}
            onChange={handleSenderEmailChange}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-primary-a50)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '6px',
              fontSize: '1rem'
            }}
          />
        </div>

        <div 
          className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          style={{
            padding: '3rem',
            border: `2px dashed ${dragActive ? 'var(--clr-primary-a40)' : 'var(--clr-surface-a30)'}`,
            borderRadius: '12px',
            backgroundColor: dragActive ? 'var(--clr-surface-tonal-a10)' : 'var(--clr-surface-a20)',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            marginBottom: '2rem'
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: '0 0 1rem 0' }}>
              Glissez et déposez votre fichier ici<br />
              ou cliquez pour sélectionner
            </p>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {progress > 0 && (
          <div className="progress-container" style={{
            marginBottom: '1rem'
          }}>
            <div className="progress-bar" style={{
              height: '4px',
              backgroundColor: 'var(--clr-surface-a30)',
              borderRadius: '2px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: 'var(--clr-primary-a40)',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <p style={{ 
              margin: '0.5rem 0 0 0',
              fontSize: '0.9rem'
            }}>
              {progress}% uploadé
            </p>
            <button 
              onClick={cancelUpload}
              style={{
                backgroundColor: 'var(--clr-surface-a30)',
                fontSize: '0.9rem',
                padding: '8px 16px'
              }}
            >
              Annuler
            </button>
          </div>
        )}

        <button 
          onClick={handleUpload}
          style={{
            width: '100%',
            padding: '1rem',
            fontSize: '1.1rem',
            backgroundColor: 'var(--clr-primary-a30)',
            transition: 'all 0.3s ease'
          }}
        >
          Envoyer le fichier
        </button>
      </div>
    </div>
  );
}

export default App;

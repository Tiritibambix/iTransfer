import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: 'var(--clr-surface-a10)',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px'
  },
  inputContainer: {
    width: '100%',
    maxWidth: '400px'
  },
  emailInput: {
    width: '100%',
    padding: '12px',
    backgroundColor: 'var(--clr-surface-a20)',
    border: 'none',
    borderRadius: '5px',
    color: 'var(--clr-primary-a50)',
    marginBottom: '10px'
  },
  fileInput: {
    display: 'none'
  },
  fileLabel: {
    display: 'block',
    padding: '12px 20px',
    backgroundColor: 'var(--clr-surface-a20)',
    color: 'var(--clr-primary-a50)',
    borderRadius: '5px',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'background-color 0.3s',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  progressContainer: {
    width: '100%',
    maxWidth: '400px',
    margin: '20px auto'
  },
  progressBar: {
    width: '100%',
    height: '12px',
    backgroundColor: 'var(--clr-surface-a20)',
    borderRadius: '6px',
    overflow: 'hidden',
    boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.2)'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, var(--clr-primary-a30) 0%, var(--clr-primary-a40) 100%)',
    borderRadius: '6px',
    transition: 'width 0.3s ease-in-out',
    position: 'relative'
  },
  progressText: {
    position: 'absolute',
    right: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    fontSize: '10px',
    color: 'white',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)'
  },
  uploadButton: {
    minWidth: '150px',
    padding: '10px 20px',
    backgroundColor: 'var(--clr-primary-a30)',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'background-color 0.3s'
  },
  settingsLink: {
    display: 'inline-block',
    marginTop: '20px',
    fontSize: '12px',
    color: 'var(--clr-primary-a40)',
    textDecoration: 'none',
    opacity: 0.7,
    transition: 'opacity 0.3s'
  }
};

function App({ backendUrl }) {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const xhrRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setProgress(0);
  };

  const handleUpload = () => {
    if (!selectedFile || !recipientEmail) {
      alert('Veuillez sélectionner un fichier et saisir un email');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('email', recipientEmail);

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
        if (response.email_sent) {
          alert('Le fichier a été uploadé et un email a été envoyé au destinataire.');
        } else {
          alert('Le fichier a été uploadé mais l\'envoi de l\'email a échoué.');
        }
      } else {
        alert('Erreur lors de l\'upload. Veuillez vérifier que l\'email est valide et réessayer.');
      }
      setProgress(0);
      setSelectedFile(null);
      setRecipientEmail('');
    };

    xhr.onerror = () => {
      alert('Erreur réseau lors de l\'upload');
      setProgress(0);
    };

    xhr.send(formData);
    xhrRef.current = xhr;
  };

  return (
    <div style={styles.container}>
      <h1>iTransfer</h1>
      
      <div style={styles.content}>
        <div style={styles.inputContainer}>
          <input
            type="email"
            placeholder="Email du destinataire"
            value={recipientEmail}
            onChange={(e) => setRecipientEmail(e.target.value)}
            style={styles.emailInput}
          />
          
          <input
            type="file"
            id="file"
            onChange={handleFileChange}
            style={styles.fileInput}
          />
          <label htmlFor="file" style={styles.fileLabel}>
            {selectedFile ? selectedFile.name : 'Choisir un fichier'}
          </label>
        </div>

        {progress > 0 && (
          <div style={styles.progressContainer}>
            <div style={styles.progressBar}>
              <div
                style={{
                  ...styles.progressFill,
                  width: `${progress}%`
                }}
              >
                <span style={styles.progressText}>{progress}%</span>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!selectedFile || !recipientEmail || progress > 0}
          style={{
            ...styles.uploadButton,
            opacity: (!selectedFile || !recipientEmail || progress > 0) ? 0.5 : 1,
            cursor: (!selectedFile || !recipientEmail || progress > 0) ? 'not-allowed' : 'pointer'
          }}
        >
          {progress > 0 ? 'Envoi en cours...' : 'Envoyer'}
        </button>
      </div>

      <Link to="/smtp-settings" style={styles.settingsLink}>
        Paramètres SMTP
      </Link>
    </div>
  );
}

export default App;

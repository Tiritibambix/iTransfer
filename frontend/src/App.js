import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: 'var(--clr-surface-a10)',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    textAlign: 'center'
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px',
    width: '100%'
  },
  inputContainer: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px'
  },
  emailInput: {
    width: '90%',
    padding: '15px',
    backgroundColor: 'var(--clr-surface-a20)',
    border: '1px solid var(--clr-surface-a30)',
    borderRadius: '4px',
    color: 'var(--clr-primary-a50)',
    fontSize: '16px'
  },
  fileInput: {
    display: 'none'
  },
  fileLabel: {
    width: '90%',
    padding: '15px',
    backgroundColor: 'var(--clr-surface-a20)',
    color: 'var(--clr-primary-a50)',
    borderRadius: '4px',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'background-color 0.3s',
    border: '1px solid var(--clr-surface-a30)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    fontSize: '16px'
  },
  progressContainer: {
    width: '90%',
    margin: '20px auto'
  },
  progressBar: {
    width: '100%',
    height: '15px',
    backgroundColor: 'var(--clr-surface-a20)',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.2)'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, var(--clr-primary-a30) 0%, var(--clr-primary-a40) 100%)',
    borderRadius: '8px',
    transition: 'width 0.3s ease-in-out',
    position: 'relative'
  },
  progressText: {
    position: 'absolute',
    right: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    fontSize: '12px',
    color: 'white',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)'
  },
  uploadButton: {
    width: '90%',
    padding: '15px',
    backgroundColor: 'var(--clr-primary-a30)',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'background-color 0.3s',
    fontSize: '16px'
  },
  settingsLink: {
    display: 'inline-block',
    marginTop: '30px',
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
            name="recipientEmail"
            placeholder="Email du destinataire"
            value={recipientEmail}
            onChange={(e) => setRecipientEmail(e.target.value)}
            style={styles.emailInput}
            autoComplete="email"
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

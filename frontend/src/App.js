import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

function App() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [fileList, setFileList] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState('');
  const xhrRef = useRef(null);
  const fileInputRef = useRef(null);
  const backendUrl = window.BACKEND_URL;

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);

    let items;
    if (e.dataTransfer.items) {
      items = [...e.dataTransfer.items];
    } else {
      items = [...e.dataTransfer.files];
    }

    processItems(items);
  }, []);

  const processItems = async (items) => {
    const allFiles = [];
    const fileList = [];

    const processItem = async (item) => {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          allFiles.push(file);
          fileList.push({ 
            name: file.name, 
            path: file.webkitRelativePath || file.name,
            size: file.size 
          });
        }
      } else if (item.isDirectory) {
        const reader = item.createReader();
        const entries = await new Promise((resolve) => {
          reader.readEntries(resolve);
        });
        for (const entry of entries) {
          await processItem(entry);
        }
      }
    };

    for (const item of items) {
      if (item.kind === 'file' || item.isDirectory) {
        await processItem(item);
      } else if (item instanceof File) {
        allFiles.push(item);
        fileList.push({ 
          name: item.name, 
          path: item.webkitRelativePath || item.name,
          size: item.size 
        });
      }
    }

    setSelectedFiles(allFiles);
    setFileList(fileList);
  };

  const handleFileSelect = (e) => {
    const files = [...e.target.files];
    processItems(files);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFiles.length || !recipientEmail || !senderEmail) {
      alert('Veuillez sélectionner au moins un fichier et remplir les adresses email');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('email', recipientEmail);
    formData.append('sender_email', senderEmail);
    
    // Ajout de tous les fichiers sélectionnés
    selectedFiles.forEach((file, index) => {
      formData.append('files[]', file);
      formData.append('paths[]', fileList[index].path);
    });

    try {
      console.log('Fichiers à envoyer :', fileList.map(f => f.path));
      console.log('Email du destinataire :', recipientEmail);
      console.log('Email de l\'expéditeur :', senderEmail);

      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });

      if (response.ok) {
        setMessage('Fichiers envoyés avec succès !');
        setSelectedFiles([]);
        setFileList([]);
        setUploadProgress(0);
      } else {
        const error = await response.json();
        setMessage(error.error || 'Erreur lors de l\'upload');
      }
    } catch (error) {
      console.error('Erreur:', error);
      setMessage('Erreur lors de l\'upload. Veuillez vérifier que les emails sont valides et réessayer.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRecipientEmailChange = (event) => {
    setRecipientEmail(event.target.value);
  };

  const handleSenderEmailChange = (event) => {
    setSenderEmail(event.target.value);
  };

  return (
    <div className="container" style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: 'clamp(1rem, 3vw, 2rem)',
      backgroundColor: 'var(--clr-surface-a10)',
      borderRadius: '12px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    }}>
      <h1 style={{
        fontSize: 'clamp(1.5rem, 4vw, 2rem)',
        marginBottom: 'clamp(1.5rem, 4vw, 2rem)',
        color: 'var(--clr-text)',
        textAlign: 'center'
      }}>
        iTransfer
      </h1>

      <div className="email-inputs" style={{
        display: 'grid',
        gap: 'clamp(1rem, 3vw, 1.5rem)',
        marginBottom: 'clamp(1.5rem, 4vw, 2rem)'
      }}>
        <div>
          <label htmlFor="recipientEmail" style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: 'var(--clr-text)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)'
          }}>
            Email du destinataire
          </label>
          <input
            type="email"
            id="recipientEmail"
            value={recipientEmail}
            onChange={handleRecipientEmailChange}
            style={{
              width: '100%',
              padding: 'clamp(0.5rem, 2vw, 0.75rem)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '4px',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-text)',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)'
            }}
          />
        </div>

        <div>
          <label htmlFor="senderEmail" style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: 'var(--clr-text)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)'
          }}>
            Votre email
          </label>
          <input
            type="email"
            id="senderEmail"
            value={senderEmail}
            onChange={handleSenderEmailChange}
            style={{
              width: '100%',
              padding: 'clamp(0.5rem, 2vw, 0.75rem)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '4px',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-text)',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)'
            }}
          />
        </div>
      </div>

      <div 
        className="drop-zone" 
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragEnter={() => setDragActive(true)}
        onDragLeave={() => setDragActive(false)}
        style={{
          border: '2px dashed var(--clr-surface-a30)',
          borderRadius: '8px',
          padding: 'clamp(2rem, 6vw, 3rem)',
          backgroundColor: dragActive ? 'var(--clr-surface-a30)' : 'var(--clr-surface-a20)',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          marginBottom: 'clamp(1.5rem, 4vw, 2rem)',
          textAlign: 'center'
        }}
      >
        <input
          type="file"
          onChange={handleFileSelect}
          multiple
          webkitdirectory=""
          directory=""
          style={{ display: 'none' }}
          id="file-upload"
        />
        <div>
          <p style={{ 
            marginBottom: 'clamp(1rem, 3vw, 1.5rem)',
            color: 'var(--clr-text)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)'
          }}>
            Glissez-déposez vos fichiers ou dossiers ici ou
            <label 
              htmlFor="file-upload" 
              style={{ 
                color: 'var(--clr-primary)',
                cursor: 'pointer',
                marginLeft: '0.5rem',
                textDecoration: 'underline'
              }}
            >
              parcourez
            </label>
          </p>
          {fileList.length > 0 && (
            <div style={{ 
              marginTop: 'clamp(1rem, 3vw, 1.5rem)',
              textAlign: 'left',
              maxHeight: '200px',
              overflowY: 'auto',
              padding: 'clamp(1rem, 3vw, 1.5rem)',
              backgroundColor: 'var(--clr-surface-a10)',
              borderRadius: '4px',
              border: '1px solid var(--clr-surface-a30)'
            }}>
              <h4 style={{ 
                marginBottom: 'clamp(0.5rem, 2vw, 1rem)',
                color: 'var(--clr-text)',
                fontSize: 'clamp(0.875rem, 2vw, 1rem)',
                fontWeight: '600'
              }}>
                Fichiers sélectionnés ({fileList.length}):
              </h4>
              {fileList.map((file, index) => (
                <div key={index} style={{ 
                  fontSize: 'clamp(0.75rem, 1.8vw, 0.875rem)',
                  marginBottom: '0.5rem',
                  color: 'var(--clr-text-secondary)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ wordBreak: 'break-all', marginRight: '1rem' }}>{file.path}</span>
                  <span style={{ whiteSpace: 'nowrap' }}>({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {isUploading && (
        <div className="progress-container" style={{
          marginBottom: 'clamp(1.5rem, 4vw, 2rem)'
        }}>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: 'var(--clr-surface-a20)',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${uploadProgress}%`,
              height: '100%',
              backgroundColor: 'var(--clr-primary)',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <p style={{
            margin: '0.5rem 0 0 0',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)',
            color: 'var(--clr-text-secondary)',
            textAlign: 'center'
          }}>
            {uploadProgress}% uploadé
          </p>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!fileList.length || !recipientEmail || !senderEmail || isUploading}
        style={{
          width: '100%',
          padding: 'clamp(0.75rem, 2.5vw, 1rem)',
          backgroundColor: (!fileList.length || !recipientEmail || !senderEmail || isUploading) 
            ? 'var(--clr-surface-a30)' 
            : 'var(--clr-primary)',
          color: (!fileList.length || !recipientEmail || !senderEmail || isUploading)
            ? 'var(--clr-text-secondary)'
            : 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: (!fileList.length || !recipientEmail || !senderEmail || isUploading)
            ? 'not-allowed'
            : 'pointer',
          fontSize: 'clamp(0.875rem, 2vw, 1rem)',
          fontWeight: '500',
          transition: 'all 0.3s ease'
        }}
      >
        {isUploading ? 'Envoi en cours...' : 'Envoyer les fichiers'}
      </button>

      {message && (
        <p style={{ 
          marginTop: 'clamp(1rem, 3vw, 1.5rem)',
          textAlign: 'center',
          color: message.includes('succès') ? 'var(--clr-success)' : 'var(--clr-error)',
          fontSize: 'clamp(0.875rem, 2vw, 1rem)'
        }}>
          {message}
        </p>
      )}
    </div>
  );
}

export default App;

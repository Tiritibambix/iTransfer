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
    <div className="app-container" style={{
      padding: 'clamp(1rem, 3vw, 2rem)',
      maxWidth: '800px',
      width: '100%',
      margin: '0 auto',
      boxSizing: 'border-box'
    }}>
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 'clamp(1rem, 3vw, 2rem)',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <h1 style={{
          fontSize: 'clamp(1.5rem, 5vw, 2.5rem)',
          margin: 0,
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          flex: '1 1 auto'
        }}>iTransfer</h1>
        <button 
          onClick={() => navigate('/smtp-settings')}
          style={{
            backgroundColor: 'var(--clr-surface-a20)',
            color: 'var(--clr-primary-a50)',
            transition: 'all 0.3s ease',
            padding: 'clamp(0.5rem, 2vw, 0.75rem) clamp(1rem, 3vw, 1.5rem)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)'
          }}
        >
          Paramètres
        </button>
      </div>

      <div className="main-content" style={{
        backgroundColor: 'var(--clr-surface-a10)',
        padding: 'clamp(1rem, 3vw, 2rem)',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      }}>
        <div className="email-inputs" style={{
          display: 'flex',
          flexDirection: window.innerWidth <= 768 ? 'column' : 'row',
          gap: 'clamp(0.5rem, 2vw, 1rem)',
          marginBottom: 'clamp(1rem, 3vw, 2rem)'
        }}>
          <input 
            type="email" 
            placeholder="Email du destinataire"
            value={recipientEmail}
            onChange={handleRecipientEmailChange}
            style={{
              flex: 1,
              padding: 'clamp(0.5rem, 2vw, 0.75rem)',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-primary-a50)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '6px',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)',
              width: '100%',
              boxSizing: 'border-box'
            }}
          />
          <input 
            type="email"
            placeholder="Votre email"
            value={senderEmail}
            onChange={handleSenderEmailChange}
            style={{
              flex: 1,
              padding: 'clamp(0.5rem, 2vw, 0.75rem)',
              backgroundColor: 'var(--clr-surface-a20)',
              color: 'var(--clr-primary-a50)',
              border: '1px solid var(--clr-surface-a30)',
              borderRadius: '6px',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)',
              width: '100%',
              boxSizing: 'border-box'
            }}
          />
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
            padding: 'var(--spacing-xl)',
            backgroundColor: dragActive ? 'var(--clr-surface-a30)' : 'var(--clr-surface-a20)',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
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
          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: 'var(--spacing-md)' }}>
              Glissez-déposez vos fichiers ou dossiers ici ou
              <label 
                htmlFor="file-upload" 
                style={{ 
                  color: 'var(--clr-primary-a40)',
                  cursor: 'pointer',
                  marginLeft: '0.5rem'
                }}
              >
                parcourez
              </label>
            </p>
            {fileList.length > 0 && (
              <div style={{ 
                marginTop: 'var(--spacing-md)',
                textAlign: 'left',
                maxHeight: '200px',
                overflowY: 'auto',
                padding: 'var(--spacing-sm)',
                backgroundColor: 'var(--clr-surface-a10)',
                borderRadius: '4px'
              }}>
                <h4 style={{ marginBottom: 'var(--spacing-sm)' }}>
                  Fichiers sélectionnés ({fileList.length}):
                </h4>
                {fileList.map((file, index) => (
                  <div key={index} style={{ 
                    fontSize: 'var(--font-size-sm)',
                    marginBottom: 'var(--spacing-xs)'
                  }}>
                    {file.path} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {isUploading && (
          <div className="progress-container" style={{
            marginBottom: 'clamp(1rem, 3vw, 2rem)'
          }}>
            <div className="progress-bar" style={{
              height: '4px',
              backgroundColor: 'var(--clr-surface-a30)',
              borderRadius: '2px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                backgroundColor: 'var(--clr-primary-a40)',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <p style={{ 
              margin: '0.5rem 0 0 0',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)'
            }}>
              {uploadProgress}% uploadé
            </p>
          </div>
        )}

        <button 
          onClick={handleSubmit}
          style={{
            width: '100%',
            padding: 'clamp(1rem, 3vw, 1.5rem)',
            fontSize: 'clamp(1rem, 3vw, 1.25rem)',
            backgroundColor: 'var(--clr-primary-a30)',
            transition: 'all 0.3s ease'
          }}
        >
          Envoyer le fichier
        </button>
        {message && (
          <p style={{ 
            marginTop: 'var(--spacing-md)',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--clr-primary-a40)'
          }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export default App;

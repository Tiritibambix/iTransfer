import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function App() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploadedItems, setUploadedItems] = useState([]);
  const [draggedFiles, setDraggedFiles] = useState(null);
  const xhrRef = useRef(null);
  const fileInputRef = useRef(null);
  const backendUrl = window.BACKEND_URL;

  const processFilesAndFolders = async (items) => {
    const allFiles = [];
    
    const readEntry = async (entry) => {
      return new Promise((resolve) => {
        if (entry.isFile) {
          entry.file(file => {
            // Conserver le chemin relatif du fichier
            file.relativePath = entry.fullPath;
            allFiles.push(file);
            resolve();
          });
        } else if (entry.isDirectory) {
          const dirReader = entry.createReader();
          dirReader.readEntries(async (entries) => {
            const promises = entries.map(entry => readEntry(entry));
            await Promise.all(promises);
            resolve();
          });
        }
      });
    };

    const promises = [];
    for (let item of items) {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry) {
          promises.push(readEntry(entry));
        }
      }
    }
    await Promise.all(promises);
    return allFiles;
  };

  const handleClick = async () => {
    if (supportsFileSystemAccess()) {
      try {
        // Solution moderne avec File System Access API
        const handles = await window.showOpenFilePicker({
          multiple: true,
          types: [
            {
              description: 'Tous les fichiers',
              accept: {'*/*': []}
            }
          ]
        });

        const files = [];
        for (const handle of handles) {
          if (handle.kind === 'directory') {
            await processDirectory(handle, '', files);
          } else {
            const file = await handle.getFile();
            files.push({
              name: file.name,
              path: '/' + file.name,
              size: file.size,
              file: file
            });
          }
        }

        if (files.length > 0) {
          setUploadedItems(prevItems => [...prevItems, ...files]);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Erreur lors de la sélection:', err);
        }
      }
    } else {
      // Solution de repli pour Firefox et Safari
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.multiple = true;
      fileInput.style.display = 'none';
      
      // Permettre la sélection de fichiers ET de dossiers
      fileInput.webkitdirectory = '';
      fileInput.directory = '';
      fileInput.multiple = true;
      
      fileInput.addEventListener('change', handleLegacyFileSelect);
      
      // Ajouter l'input au DOM temporairement
      document.body.appendChild(fileInput);
      
      // Déclencher le sélecteur de fichiers
      fileInput.click();
      
      // Nettoyer
      setTimeout(() => {
        document.body.removeChild(fileInput);
      }, 1000);
    }
  };

  const supportsFileSystemAccess = () => {
    return 'showOpenFilePicker' in window;
  };

  const handleLegacyFileSelect = async (event) => {
    event.preventDefault();
    const files = Array.from(event.target.files);
    
    if (files.length > 0) {
      const processedFiles = files.map(file => {
        // Utiliser webkitRelativePath s'il existe (cas des dossiers), sinon utiliser le nom du fichier
        const path = file.webkitRelativePath || ('/' + file.name);
        return {
          name: file.name,
          path: path,
          size: file.size,
          file: file
        };
      });
      setUploadedItems(prevItems => [...prevItems, ...processedFiles]);
    }
  };

  const processDirectory = async (dirHandle, path, files) => {
    for await (const entry of dirHandle.values()) {
      const entryPath = path ? `${path}/${entry.name}` : entry.name;
      
      if (entry.kind === 'directory') {
        await processDirectory(entry, entryPath, files);
      } else {
        const file = await entry.getFile();
        files.push({
          name: file.name,
          path: '/' + entryPath,
          size: file.size,
          file: file
        });
      }
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const processItems = async (items) => {
      const files = [];
      for (const item of items) {
        if (item.kind === 'file') {
          const entry = item.webkitGetAsEntry();
          if (entry) {
            if (entry.isDirectory) {
              await readDirectoryEntries(entry, '', files);
            } else {
              const file = item.getAsFile();
              if (file) {
                files.push({
                  name: file.name,
                  path: '/' + file.name,
                  size: file.size,
                  file: file
                });
              }
            }
          }
        }
      }
      return files;
    };

    const readDirectoryEntries = async (dirEntry, path, files) => {
      const dirReader = dirEntry.createReader();
      await new Promise((resolve, reject) => {
        const readEntries = () => {
          dirReader.readEntries(async (entries) => {
            if (entries.length === 0) {
              resolve();
            } else {
              for (const entry of entries) {
                const fullPath = path ? `${path}/${entry.name}` : entry.name;
                if (entry.isDirectory) {
                  await readDirectoryEntries(entry, fullPath, files);
                } else {
                  await new Promise((fileResolve) => {
                    entry.file((file) => {
                      files.push({
                        name: file.name,
                        path: '/' + fullPath,
                        size: file.size,
                        file: file
                      });
                      fileResolve();
                    });
                  });
                }
              }
              readEntries();
            }
          }, reject);
        };
        readEntries();
      });
    };
    
    try {
      let files = [];
      if (e.dataTransfer.items) {
        files = await processItems(Array.from(e.dataTransfer.items));
      } else {
        files = Array.from(e.dataTransfer.files).map(file => ({
          name: file.name,
          path: '/' + file.name,
          size: file.size,
          file: file
        }));
      }
      
      if (files.length > 0) {
        setUploadedItems(prevItems => [...prevItems, ...files]);
      }
    } catch (error) {
      console.error('Erreur lors du traitement des fichiers:', error);
    }
  };

  const handleFileSelect = async (event) => {
    event.preventDefault();
    const files = Array.from(event.target.files);
    
    if (files.length > 0) {
      const processedFiles = files.map(file => {
        return {
          name: file.name,
          path: '/' + file.name,
          size: file.size,
          file: file
        };
      });
      setUploadedItems(prevItems => [...prevItems, ...processedFiles]);
    }
  };

  const handleUpload = () => {
    if (uploadedItems.length === 0) {
      alert('Veuillez sélectionner au moins un fichier');
      return;
    }

    if (!recipientEmail || !senderEmail) {
      alert('Veuillez remplir les adresses email du destinataire et de l\'expéditeur');
      return;
    }

    const formData = new FormData();
    uploadedItems.forEach(item => {
      // Utiliser le fichier original stocké dans l'item
      if (item.file) {
        formData.append('files[]', item.file);
        formData.append('paths[]', item.path);
      }
    });
    formData.append('email', recipientEmail);
    formData.append('sender_email', senderEmail);

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
          alert('Les fichiers ont été uploadés mais il y a eu un problème avec l\'envoi des notifications.');
        } else {
          alert('Les fichiers ont été uploadés et les notifications ont été envoyées.');
        }
        setUploadedItems([]);
        setDraggedFiles(null);
        setProgress(0);
      } else {
        console.error('Erreur lors de l\'upload :', xhr.status, xhr.statusText);
        alert('Erreur lors de l\'upload. Veuillez vérifier que les emails sont valides et réessayer.');
        setProgress(0);
      }
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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleRecipientEmailChange = (event) => {
    setRecipientEmail(event.target.value);
  };

  const handleSenderEmailChange = (event) => {
    setSenderEmail(event.target.value);
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

  const cancelUpload = () => {
    if (xhrRef.current) {
      xhrRef.current.abort();
      console.log('Upload annulé');
      setProgress(0);
    }
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
          className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleClick}
          style={{
            padding: 'clamp(1.5rem, 4vw, 3rem)',
            border: '2px dashed var(--clr-surface-a30)',
            borderRadius: '8px',
            backgroundColor: dragActive ? 'var(--clr-surface-a30)' : 'var(--clr-surface-a20)',
            transition: 'all 0.3s ease',
            cursor: 'pointer',
            textAlign: 'center',
            marginBottom: 'clamp(1rem, 3vw, 2rem)'
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: '0 0 1rem 0' }}>
              Glissez et déposez vos fichiers et dossiers ici<br />
              ou cliquez pour sélectionner des fichiers et dossiers
            </p>
          </div>
        </div>

        {uploadedItems.length > 0 && (
          <div style={{
            backgroundColor: 'var(--clr-surface-a20)',
            padding: 'clamp(1rem, 3vw, 1.5rem)',
            borderRadius: '8px',
            marginBottom: 'clamp(1rem, 3vw, 2rem)'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem'
            }}>
              <h3 style={{
                margin: '0',
                fontSize: 'clamp(1rem, 2.5vw, 1.25rem)'
              }}>
                Fichiers sélectionnés :
              </h3>
              <button
                onClick={() => {
                  setUploadedItems([]);
                  setDraggedFiles(null);
                }}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'var(--clr-surface-a30)',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  color: 'var(--clr-text)',
                  fontSize: '0.9rem'
                }}
              >
                Effacer la sélection
              </button>
            </div>
            <div style={{
              maxHeight: '200px',
              overflowY: 'auto',
              padding: '0.5rem'
            }}>
              {uploadedItems.map((item, index) => (
                <div key={index} style={{
                  padding: '0.5rem',
                  borderBottom: index < uploadedItems.length - 1 ? '1px solid var(--clr-surface-a30)' : 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontSize: '0.9rem' }}>{item.path}</div>
                    <div style={{ 
                      fontSize: '0.8rem',
                      color: 'var(--clr-primary-a40)'
                    }}>
                      {formatFileSize(item.size)}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setUploadedItems(prevItems => prevItems.filter((_, i) => i !== index));
                    }}
                    style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      color: 'var(--clr-text-a60)',
                      fontSize: '0.8rem'
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {progress > 0 && (
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
                width: `${progress}%`,
                height: '100%',
                backgroundColor: 'var(--clr-primary-a40)',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <p style={{ 
              margin: '0.5rem 0 0 0',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)'
            }}>
              {progress}% uploadé
            </p>
            <button 
              onClick={cancelUpload}
              style={{
                backgroundColor: 'var(--clr-surface-a30)',
                fontSize: 'clamp(0.875rem, 2vw, 1rem)',
                padding: 'clamp(0.5rem, 2vw, 0.75rem) clamp(1rem, 3vw, 1.5rem)'
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
            padding: 'clamp(1rem, 3vw, 1.5rem)',
            fontSize: 'clamp(1rem, 3vw, 1.25rem)',
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

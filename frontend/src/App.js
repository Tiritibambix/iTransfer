import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import JSZip from 'jszip';
import banner from './assets/iTransfer Bannière.png';

function App() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [expirationDays, setExpirationDays] = useState(7);
  const [dragActive, setDragActive] = useState(false);
  const [uploadedItems, setUploadedItems] = useState([]);
  const [draggedFiles, setDraggedFiles] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [warning, setWarning] = useState(null);
  const [compressionProgress, setCompressionProgress] = useState(0);
  const [isCompressing, setIsCompressing] = useState(false);
  const xhrRef = useRef(null);
  const fileInputRef = useRef(null);
  const backendUrl = window.BACKEND_URL;

  // Demander la permission des notifications au chargement
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  // Gestion de la prévention de fermeture pendant l'upload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isCompressing || (progress > 0 && progress < 100)) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    if (isCompressing || (progress > 0 && progress < 100)) {
      window.addEventListener('beforeunload', handleBeforeUnload);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isCompressing, progress]);

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
    // Solution simplifiée pour la sélection de fichiers uniquement
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.style.display = 'none';
    
    fileInput.addEventListener('change', handleLegacyFileSelect);
    
    // Ajouter l'input au DOM temporairement
    document.body.appendChild(fileInput);
    
    // Déclencher le sélecteur de fichiers
    fileInput.click();
    
    // Nettoyer
    setTimeout(() => {
      document.body.removeChild(fileInput);
    }, 1000);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const processItems = async (items) => {
      const files = [];
      const processEntry = async (entry, basePath = '') => {
        if (entry.isFile) {
          return new Promise((resolve, reject) => {
            entry.file(file => {
              // Si le fichier est dans un dossier, on garde le chemin complet
              const relativePath = basePath ? `/${basePath}/${file.name}` : `/${file.name}`;
              files.push({
                name: file.name,
                path: relativePath,
                size: file.size,
                file: file,
                // Ajouter le dossier parent pour une meilleure organisation
                parentFolder: basePath.split('/')[0] || ''
              });
              resolve();
            }, reject);
          });
        } else if (entry.isDirectory) {
          const dirReader = entry.createReader();
          return new Promise((resolve, reject) => {
            const readEntries = () => {
              dirReader.readEntries(async (entries) => {
                if (entries.length === 0) {
                  resolve();
                } else {
                  const promises = entries.map(entry => {
                    // Pour les dossiers, on construit le chemin en ajoutant le nom du dossier actuel
                    const newPath = basePath ? `${basePath}/${entry.name}` : entry.name;
                    return processEntry(entry, newPath);
                  });
                  await Promise.all(promises);
                  readEntries();
                }
              }, reject);
            };
            readEntries();
          });
        }
      };

      const promises = [];
      for (const item of items) {
        if (item.kind === 'file') {
          const entry = item.webkitGetAsEntry();
          if (entry) {
            // Si c'est un dossier, on utilise son nom comme basePath
            const basePath = entry.isDirectory ? entry.name : '';
            promises.push(processEntry(entry, basePath));
          } else {
            const file = item.getAsFile();
            if (file) {
              files.push({
                name: file.name,
                path: `/${file.name}`,
                size: file.size,
                file: file,
                parentFolder: ''
              });
            }
          }
        }
      }
      
      await Promise.all(promises);

      // Grouper les fichiers par dossier parent
      const groupedFiles = files.reduce((acc, file) => {
        const key = file.parentFolder || '';
        if (!acc[key]) {
          acc[key] = [];
        }
        acc[key].push(file);
        return acc;
      }, {});

      // Aplatir la structure en conservant l'organisation des dossiers
      const organizedFiles = Object.values(groupedFiles).flat();
      
      return organizedFiles;
    };

    try {
      let files = [];
      if (e.dataTransfer.items) {
        files = await processItems(Array.from(e.dataTransfer.items));
      } else {
        files = Array.from(e.dataTransfer.files).map(file => ({
          name: file.name,
          path: `/${file.name}`,
          size: file.size,
          file: file,
          parentFolder: ''
        }));
      }
      
      if (files.length > 0) {
        console.log('Structure des fichiers:', files.map(f => ({ 
          name: f.name, 
          path: f.path, 
          parentFolder: f.parentFolder 
        })));
        setUploadedItems(prevItems => [...prevItems, ...files]);
      }
    } catch (error) {
      console.error('Erreur lors du traitement des fichiers:', error);
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

  const generateZipName = () => {
    const now = new Date();
    const year = now.getFullYear().toString().slice(-2);
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `iTransfer_${year}${month}${day}${hours}${minutes}.zip`;
  };

  const handleUpload = async () => {
    if (uploadedItems.length === 0) {
      showNotification("Veuillez sélectionner au moins un fichier", "error");
      return;
    }

    if (!recipientEmail) {
      showNotification("Veuillez remplir l'adresse email du destinataire", "error");
      return;
    }

    if (!senderEmail) {
      showNotification("Veuillez remplir votre adresse email", "error");
      return;
    }

    setError(null);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('email', recipientEmail);
      formData.append('sender_email', senderEmail);
      formData.append('expiration_days', expirationDays);

      // Préparer la liste des fichiers pour les emails
      const filesList = uploadedItems.map(item => ({
        name: item.path.substring(1),
        size: item.file.size
      }));
      formData.append('files_list', JSON.stringify(filesList));

      // Si plusieurs fichiers, on compresse
      if (uploadedItems.length > 1) {
        setIsCompressing(true);
        const zip = new JSZip();
        
        // Ajouter chaque fichier au zip
        for (let i = 0; i < uploadedItems.length; i++) {
          const item = uploadedItems[i];
          zip.file(item.path.substring(1), item.file);
          // Mise à jour de la progression de compression
          setCompressionProgress(Math.round((i + 1) * 100 / uploadedItems.length));
        }

        // Générer le zip avec compression
        const zipBlob = await zip.generateAsync({ 
          type: "blob",
          compression: "DEFLATE",
          compressionOptions: { level: 6 }
        }, (metadata) => {
          setCompressionProgress(Math.round(metadata.percent));
        });

        const zipName = generateZipName();
        formData.append('files[]', zipBlob, zipName);
        formData.append('paths[]', '/' + zipName);
        setIsCompressing(false);
      } else {
        // Un seul fichier, pas de compression
        uploadedItems.forEach((item) => {
          formData.append('files[]', item.file);
          formData.append('paths[]', item.path);
        });
      }

      setUploading(true);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${backendUrl}/upload`, true);
      
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentCompleted = Math.round((event.loaded * 100) / event.total);
          setProgress(percentCompleted);
        }
      };

      xhr.onload = function() {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          if (response.warning) {
            showNotification("Les fichiers ont été uploadés mais il y a eu un problème avec l'envoi des notifications.", "warning");
          } else {
            showNotification("Les fichiers ont été uploadés et les notifications ont été envoyées avec succès !", "success");
          }
        } else {
          showNotification("Une erreur est survenue lors de l'upload. Veuillez vérifier que les emails sont valides et réessayer.", "error");
        }
        setUploading(false);
      };

      xhr.onerror = function() {
        showNotification("Une erreur réseau est survenue. Veuillez vérifier votre connexion et réessayer.", "error");
        setUploading(false);
      };

      xhr.send(formData);
      xhrRef.current = xhr;
    } catch (error) {
      console.error('Erreur:', error);
      showNotification("Une erreur est survenue lors de l'upload", "error");
      setUploading(false);
      setIsCompressing(false);
    }
  };

  const resetUploadState = () => {
    setProgress(0);
    setCompressionProgress(0);
    setIsCompressing(false);
    setUploading(false);
    setUploadedItems([]);
    setRecipientEmail('');
    setSenderEmail('');
    setError(null);
    setWarning(null);
    setSuccess(false);
  };

  const showNotification = (message, type = 'info') => {
    // Log pour debug
    console.log(`Notification (${type}):`, message);
    
    // Préfixer le message selon le type
    let prefix = '';
    switch (type) {
        case 'error':
            prefix = '❌ Erreur : ';
            break;
        case 'success':
            prefix = '✅ Succès : ';
            break;
        case 'warning':
            prefix = '⚠️ Attention : ';
            break;
        default:
            prefix = 'ℹ️ Info : ';
    }
    
    // Afficher l'alerte et réinitialiser si succès
    alert(prefix + message);
    if (type === 'success') {
      resetUploadState();
    }
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
      xhrRef.current = null;
    }
    setUploading(false);
    setProgress(0);
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
        gap: 'clamp(0.5rem, 2vw, 1rem)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'clamp(0.5rem, 2vw, 1rem)',
          flex: '1 1 auto',
          minWidth: '200px'
        }}>
          <img 
            src={banner}
            alt="iTransfer"
            style={{
              height: 'clamp(2rem, 6vw, 3rem)',
              width: 'auto',
              objectFit: 'contain'
            }}
          />
        </div>
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

        <div style={{
          marginBottom: 'clamp(1rem, 3vw, 1.5rem)',
          backgroundColor: 'var(--clr-surface-a20)',
          padding: 'clamp(0.75rem, 2vw, 1rem)',
          borderRadius: '6px'
        }}>
          <label style={{
            display: 'block',
            marginBottom: 'clamp(0.5rem, 1vw, 0.75rem)',
            color: 'var(--clr-primary-a40)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)'
          }}>
            Expiration du lien
          </label>
          <select
            value={expirationDays}
            onChange={(e) => setExpirationDays(parseInt(e.target.value))}
            style={{
              width: '100%',
              padding: 'clamp(0.5rem, 2vw, 0.75rem)',
              backgroundColor: 'var(--clr-surface-a30)',
              color: 'var(--clr-primary-a50)',
              border: '1px solid var(--clr-surface-a40)',
              borderRadius: '4px',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)'
            }}
          >
            <option value="3">3 jours</option>
            <option value="5">5 jours</option>
            <option value="7">7 jours</option>
            <option value="10">10 jours</option>
          </select>
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
              ou cliquez pour sélectionner des fichiers uniquement
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

        {(isCompressing || progress > 0) && (
          <div style={{
            backgroundColor: 'var(--clr-surface-a20)',
            padding: 'clamp(1rem, 3vw, 1.5rem)',
            borderRadius: '8px',
            marginBottom: 'clamp(1rem, 3vw, 2rem)'
          }}>
            <div className="progress-container">
              <div
                className="progress-bar"
                style={{
                  width: `${isCompressing ? compressionProgress : progress}%`
                }}
              />
              <div className="progress-info">
                <span className="progress-text">
                  {isCompressing
                    ? `Compression : ${compressionProgress}%`
                    : `Upload : ${progress}%`}
                </span>
                <button
                  className="cancel-button"
                  onClick={cancelUpload}
                  aria-label="Annuler"
                >
                  Annuler
                </button>
              </div>
            </div>
            <div style={{
              marginTop: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--clr-primary-a50)',
              fontSize: '0.9rem',
              padding: '0.5rem',
              backgroundColor: 'var(--clr-surface-a30)',
              borderRadius: '4px',
              border: '1px solid var(--clr-primary-a20)'
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-1-7v2h2v-2h-2zm0-8v6h2V7h-2z"
                  fill="currentColor"/>
              </svg>
              <span>
                {isCompressing
                  ? "Compression en cours. Veuillez ne pas fermer cette fenêtre."
                  : "Transfert en cours. Veuillez ne pas fermer cette fenêtre."}
              </span>
            </div>
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

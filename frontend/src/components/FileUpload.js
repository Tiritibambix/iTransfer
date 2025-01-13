import React, { useState, useRef } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

const FileUpload = () => {
    const [files, setFiles] = useState([]);
    const [email, setEmail] = useState('');
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const onDrop = acceptedFiles => {
        setFiles(acceptedFiles);
        setError(null);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: true
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!files.length) {
            setError('Veuillez sélectionner au moins un fichier');
            return;
        }
        
        if (!email) {
            setError('Veuillez entrer une adresse email');
            return;
        }

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files[]', file);
        });
        formData.append('email', email);

        setUploading(true);
        setError(null);
        
        try {
            const response = await axios.post(
                `${process.env.REACT_APP_API_URL}/upload`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    },
                    onUploadProgress: (progressEvent) => {
                        const percentCompleted = Math.round(
                            (progressEvent.loaded * 100) / progressEvent.total
                        );
                        setProgress(percentCompleted);
                    }
                }
            );

            setSuccess(`Fichier${files.length > 1 ? 's' : ''} envoyé${files.length > 1 ? 's' : ''} avec succès !`);
            setFiles([]);
            setEmail('');
            
        } catch (err) {
            setError(err.response?.data?.error || 'Erreur lors de l\'upload');
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    return (
        <div className="upload-container">
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                {isDragActive ? (
                    <p>Déposez les fichiers ici...</p>
                ) : (
                    <p>Glissez-déposez des fichiers ici, ou cliquez pour sélectionner</p>
                )}
            </div>

            {files.length > 0 && (
                <div className="selected-files">
                    <h4>Fichiers sélectionnés :</h4>
                    <ul>
                        {files.map((file, index) => (
                            <li key={index}>
                                {file.name} ({(file.size / 1024).toFixed(2)} KB)
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    placeholder="Email du destinataire"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <button type="submit" disabled={uploading || !files.length}>
                    {uploading ? 'Envoi en cours...' : 'Envoyer'}
                </button>
            </form>

            {uploading && (
                <div className="progress-bar">
                    <div 
                        className="progress"
                        style={{ width: `${progress}%` }}
                    />
                    <span>{progress}%</span>
                </div>
            )}

            {error && <div className="error">{error}</div>}
            {success && <div className="success">{success}</div>}
        </div>
    );
};

export default FileUpload;

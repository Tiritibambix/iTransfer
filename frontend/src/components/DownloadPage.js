import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

const DownloadPage = () => {
    const { fileId } = useParams();
    const [fileDetails, setFileDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchFileDetails();
    }, [fileId]);

    const fetchFileDetails = async () => {
        try {
            const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/files/${fileId}`);
            setFileDetails(response.data);
        } catch (err) {
            setError('Impossible de charger les détails du fichier');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            window.location.href = `${process.env.REACT_APP_API_URL}/download/${fileId}`;
        } catch (err) {
            setError('Erreur lors du téléchargement');
        }
    };

    if (loading) return <div>Chargement...</div>;
    if (error) return <div className="error">{error}</div>;
    if (!fileDetails) return <div>Fichier non trouvé</div>;

    return (
        <div className="download-page">
            <h2>Fichier à télécharger</h2>
            <div className="file-details">
                <h3>{fileDetails.filename}</h3>
                
                {fileDetails.is_archive && (
                    <div className="archive-contents">
                        <h4>Contenu de l'archive :</h4>
                        <ul>
                            {fileDetails.contents.map((item, index) => (
                                <li key={index}>
                                    {item.path} ({(item.size / 1024).toFixed(2)} KB)
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <button 
                    className="download-button"
                    onClick={handleDownload}
                >
                    Télécharger
                </button>
            </div>
        </div>
    );
};

export default DownloadPage;

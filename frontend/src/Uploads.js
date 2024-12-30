import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressBar from './ProgressBar';

function Upload() {
    const [file, setFile] = useState(null);
    const [email, setEmail] = useState("");
    const [progress, setProgress] = useState(0);
    const navigate = useNavigate();

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        if (!file) {
            console.error("No file selected");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('email', email);

        try {
            const response = await fetch('http://backend:5000/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            if (response.ok) {
                navigate('/progress', { state: { progress } });
            } else {
                console.error(data.error);
            }
        } catch (error) {
            console.error("Error during upload:", error);
        }
    };

    return (
        <div>
            <h1>Upload File</h1>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleUpload}>Upload</button>
            <ProgressBar progress={progress} />
        </div>
    );
}

export default Upload;

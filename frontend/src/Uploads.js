import React, { useState } from 'react';
import ProgressBar from './ProgressBar';

function Upload() {
    const [file, setFile] = useState(null);
    const [email, setEmail] = useState("");

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('email', email);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        // Logic to handle response
    };

    return (
        <div>
            <h1>Upload File</h1>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleUpload}>Upload</button>
            <ProgressBar />
        </div>
    );
}

export default Upload;

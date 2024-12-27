import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import './index.css';

const App = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    setMessage(data.message);
  };

  return (
    <div>
      <h1>iTransfer</h1>  {/* Titre mis à jour ici */}
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {message && <p>{message}</p>}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));

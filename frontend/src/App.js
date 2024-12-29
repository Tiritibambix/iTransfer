import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FileManager from './FileManager';
import Uploads from './Uploads';

const App = () => {
  const [error, setError] = useState(null);

  const handleError = (message) => {
    setError(message);
    setTimeout(() => setError(null), 3000); // Efface l'erreur après 3 secondes
  };

  return (
    <Router>
      <div>
        {error && <div className="error-banner">{error}</div>}
        <Routes>
          <Route path="/" element={<FileManager onError={handleError} />} />
          <Route path="/uploads" element={<Uploads onError={handleError} />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;

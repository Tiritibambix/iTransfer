import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Redirect, Switch } from 'react-router-dom';
import './index.css';
import Admin from './Admin'; // Admin page (login)
import Uploads from './Uploads'; // Page pour uploader les fichiers
import ProgressBar from './ProgressBar'; // Si tu veux garder la barre de progression

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);  // Gérer l'authentification
  const [progress, setProgress] = useState(0);  // Gérer la progression de l'upload

  // Si l'utilisateur est authentifié
  useEffect(() => {
    const isAuthenticated = localStorage.getItem('isAuthenticated');
    if (isAuthenticated === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  // Fonction de login
  const handleLogin = (username, password) => {
    fetch('http://localhost:5000/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
      .then((response) => {
        if (response.ok) {
          localStorage.setItem('isAuthenticated', 'true');  // Stocke dans localStorage
          setIsAuthenticated(true);  // Mettre à jour l'état
        } else {
          alert('Nom d\'utilisateur ou mot de passe incorrect');
        }
      });
  };

  // Fonction de déconnexion
  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
  };

  // Fonction pour gérer l'upload de fichiers
  const handleFileUpload = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://localhost:5000/upload', true);

    // Gérer la progression de l'upload
    xhr.upload.onprogress = function (event) {
      if (event.lengthComputable) {
        const percent = (event.loaded / event.total) * 100;
        setProgress(percent);
      }
    };

    // Gérer la réponse de l'upload
    xhr.onload = function () {
      if (xhr.status === 200) {
        alert('Upload réussi');
      } else {
        alert('Erreur d\'upload');
      }
      setProgress(0);  // Réinitialiser la progression après l'upload
    };

    xhr.send(formData);
  };

  return (
    <Router>
      <div className="App">
        <Switch>
          {/* Route pour le login */}
          <Route
            path="/login"
            render={() => (isAuthenticated ? <Redirect to="/upload" /> : <Admin onLogin={handleLogin} />)}
          />
          
          {/* Route pour la page d'upload (protéger par l'authentification) */}
          <Route
            path="/upload"
            render={() =>
              isAuthenticated ? (
                <div>
                  <Uploads onFileUpload={handleFileUpload} />
                  <ProgressBar progress={progress} />
                  <button onClick={handleLogout}>Se déconnecter</button>
                </div>
              ) : (
                <Redirect to="/login" />
              )
            }
          />
          
          {/* Redirection vers la page de login par défaut */}
          <Redirect from="/" to="/login" />
        </Switch>
      </div>
    </Router>
  );
}

export default App;

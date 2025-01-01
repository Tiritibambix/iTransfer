import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';

// Détecter l'URL du backend dynamiquement
const backendUrl =
  window.location.hostname === 'localhost'
    ? 'http://localhost:5000'  // Remplace par le port backend de Docker
    : `http://${window.location.hostname}:5000`;  // Pour d'autres machines

console.log('Backend URL configurée :', backendUrl);

ReactDOM.render(
  <React.StrictMode>
    <App backendUrl={backendUrl} />
  </React.StrictMode>,
  document.getElementById('root')
);

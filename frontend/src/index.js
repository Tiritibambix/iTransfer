import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';

// Détecter l'URL du backend dynamiquement, avec le port 5500
const backendUrl =
  window.location.hostname === 'localhost'
    ? 'http://localhost:5500'  // Backend sur port 5500
    : `http://${window.location.hostname}:5500`;  // Pour d'autres machines

console.log('Backend URL configurée :', backendUrl);

ReactDOM.render(
  <React.StrictMode>
    <App backendUrl={backendUrl} />
  </React.StrictMode>,
  document.getElementById('root')
);

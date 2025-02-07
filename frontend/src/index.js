import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import App from './App';
import Login from './Login';
import PrivateRoute from './PrivateRoute';
import SMTPSettings from './SMTPSettings';
import Download from './Download';
import './index.css';

const backendUrl =
  window.location.hostname === 'localhost'
    ? 'http://localhost:5500'
    : `http://${window.location.hostname}:5500`;

ReactDOM.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/login" element={<Login backendUrl={backendUrl} />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <App backendUrl={backendUrl} />
            </PrivateRoute>
          }
        />
        <Route path="/smtp-settings" element={<SMTPSettings backendUrl={backendUrl} />} />
        <Route path="/download/:transferId" element={<Download backendUrl={backendUrl} />} />
      </Routes>
    </Router>
  </React.StrictMode>,
  document.getElementById('root')
);

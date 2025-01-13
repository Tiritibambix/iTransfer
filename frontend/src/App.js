import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import DownloadPage from './components/DownloadPage';
import Admin from './components/Admin';
import Login from './components/Login';
import PrivateRoute from './components/PrivateRoute';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>iTransfer</h1>
        </header>
        
        <main>
          <Routes>
            <Route path="/" element={<FileUpload />} />
            <Route path="/download/:fileId" element={<DownloadPage />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/admin/*"
              element={
                <PrivateRoute>
                  <Admin />
                </PrivateRoute>
              }
            />
          </Routes>
        </main>
        
        <footer>
          <p>&copy; 2025 iTransfer. Tous droits réservés.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import App from './App'
import Login from './Login'
import Download from './Download'
import Admin from './Admin'
import PrivateRoute from './PrivateRoute'
import { I18nProvider } from './i18n'
import './index.css'

const root = createRoot(document.getElementById('root'))

root.render(
  <React.StrictMode>
    <I18nProvider>
      <Router>
        <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/download/:transferId" element={<Download />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <App />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <Admin />
            </PrivateRoute>
          }
        />
        </Routes>
      </Router>
    </I18nProvider>
  </React.StrictMode>
)

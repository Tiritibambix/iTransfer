import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SMTPSettings = ({ backendUrl }) => {
  const navigate = useNavigate();
  const [smtpServer, setSmtpServer] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [smtpSenderEmail, setSmtpSenderEmail] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const handleSave = async () => {
    const smtpSettings = { smtpServer, smtpPort, smtpUser, smtpPassword, smtpSenderEmail };
    try {
      const response = await fetch(`${backendUrl}/api/save-smtp-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(smtpSettings),
      });

      if (response.ok) {
        setMessage('Configuration SMTP enregistrée avec succès');
        setMessageType('success');
      } else {
        setMessage('Erreur lors de l\'enregistrement de la configuration SMTP');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Erreur réseau lors de l\'enregistrement de la configuration SMTP');
      setMessageType('error');
    }
  };

  return (
    <div className="container">
      <h1>Configuration SMTP</h1>

      {message && (
        <div className={`message message-${messageType}`}>
          {message}
        </div>
      )}

      <div>
        <label>Serveur SMTP:</label>
        <input
          type="text"
          className="input"
          value={smtpServer}
          onChange={(e) => setSmtpServer(e.target.value)}
        />
      </div>

      <div>
        <label>Port SMTP:</label>
        <input
          type="text"
          className="input"
          value={smtpPort}
          onChange={(e) => setSmtpPort(e.target.value)}
        />
      </div>

      <div>
        <label>Utilisateur SMTP:</label>
        <input
          type="text"
          className="input"
          value={smtpUser}
          onChange={(e) => setSmtpUser(e.target.value)}
        />
      </div>

      <div>
        <label>Mot de passe SMTP:</label>
        <input
          type="password"
          className="input"
          value={smtpPassword}
          onChange={(e) => setSmtpPassword(e.target.value)}
        />
      </div>

      <div>
        <label>Email de l'expéditeur:</label>
        <input
          type="email"
          className="input"
          value={smtpSenderEmail}
          onChange={(e) => setSmtpSenderEmail(e.target.value)}
        />
      </div>

      <button className="button" onClick={handleSave}>
        Enregistrer
      </button>

      <button
        className="button button-secondary"
        onClick={() => navigate('/')}
      >
        Retour à l'accueil
      </button>
    </div>
  );
};

export default SMTPSettings;

import React, { useState } from 'react';

const SMTPSettings = ({ backendUrl }) => {
  const [smtpServer, setSmtpServer] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [smtpSenderEmail, setSmtpSenderEmail] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' ou 'error'

  const handleSave = async () => {
    const smtpSettings = {
      smtpServer,
      smtpPort,
      smtpUser,
      smtpPassword,
      smtpSenderEmail,
    };

    try {
      const response = await fetch(`${backendUrl}/api/save-smtp-settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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

  const handleTest = async () => {
    try {
      setMessage('Test en cours...');
      setMessageType('info');

      const response = await fetch(`${backendUrl}/api/test-smtp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Test SMTP réussi! Vérifiez votre boîte mail.');
        setMessageType('success');
      } else {
        setMessage(`Échec du test SMTP: ${data.error}`);
        setMessageType('error');
      }
    } catch (error) {
      setMessage(`Erreur lors du test: ${error.message}`);
      setMessageType('error');
    }
  };

  return (
    <div className="smtp-settings">
      <h1>Configuration SMTP</h1>
      
      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}

      <div className="form-group">
        <label>Serveur SMTP:</label>
        <input 
          type="text" 
          value={smtpServer} 
          onChange={(e) => setSmtpServer(e.target.value)}
          placeholder="ex: ssl0.ovh.net" 
        />
      </div>
      
      <div className="form-group">
        <label>Port SMTP:</label>
        <input 
          type="text" 
          value={smtpPort} 
          onChange={(e) => setSmtpPort(e.target.value)}
          placeholder="ex: 465" 
        />
      </div>
      
      <div className="form-group">
        <label>Utilisateur SMTP:</label>
        <input 
          type="text" 
          value={smtpUser} 
          onChange={(e) => setSmtpUser(e.target.value)}
          placeholder="ex: user@domain.com" 
        />
      </div>
      
      <div className="form-group">
        <label>Mot de passe SMTP:</label>
        <input 
          type="password" 
          value={smtpPassword} 
          onChange={(e) => setSmtpPassword(e.target.value)}
          placeholder="Votre mot de passe SMTP" 
        />
      </div>
      
      <div className="form-group">
        <label>Email de l'expéditeur:</label>
        <input 
          type="email" 
          value={smtpSenderEmail} 
          onChange={(e) => setSmtpSenderEmail(e.target.value)}
          placeholder="ex: no-reply@domain.com" 
        />
      </div>

      <div className="button-group">
        <button onClick={handleSave} className="primary">Enregistrer</button>
        <button onClick={handleTest} className="secondary">Tester la configuration</button>
        <button onClick={() => window.location.href = '/'} className="tertiary">Retour à l'accueil</button>
      </div>

      <style jsx>{`
        .smtp-settings {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .form-group {
          margin-bottom: 15px;
        }
        
        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: bold;
        }
        
        .form-group input {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }
        
        .button-group {
          margin-top: 20px;
          display: flex;
          gap: 10px;
        }
        
        .message {
          padding: 10px;
          margin-bottom: 20px;
          border-radius: 4px;
        }
        
        .success {
          background-color: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }
        
        .error {
          background-color: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
        
        .info {
          background-color: #cce5ff;
          color: #004085;
          border: 1px solid #b8daff;
        }
        
        button {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        
        button.primary {
          background-color: #007bff;
          color: white;
        }
        
        button.secondary {
          background-color: #6c757d;
          color: white;
        }
        
        button.tertiary {
          background-color: #f8f9fa;
          border: 1px solid #ddd;
        }
        
        button:hover {
          opacity: 0.9;
        }
      `}</style>
    </div>
  );
};

export default SMTPSettings;

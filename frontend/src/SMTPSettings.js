import React, { useState, memo } from 'react';
import { useNavigate } from 'react-router-dom';

const InputField = memo(({ label, type = "text", value, onChange, placeholder, id }) => (
  <div className="form-group" style={{
    marginBottom: 'clamp(1rem, 3vw, 1.5rem)',
  }}>
    <label 
      htmlFor={id}
      style={{
        display: 'block',
        marginBottom: 'clamp(0.25rem, 1vw, 0.5rem)',
        color: 'var(--clr-primary-a40)',
        fontSize: 'clamp(0.8rem, 2vw, 0.9rem)'
      }}
    >
      {label}
    </label>
    <input 
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{
        width: '100%',
        padding: 'clamp(0.5rem, 2vw, 0.75rem)',
        backgroundColor: 'var(--clr-surface-a20)',
        color: 'var(--clr-primary-a50)',
        border: '1px solid var(--clr-surface-a30)',
        borderRadius: '6px',
        fontSize: 'clamp(0.875rem, 2vw, 1rem)',
        transition: 'all 0.3s ease',
        boxSizing: 'border-box'
      }}
    />
  </div>
));

const SMTPSettings = () => {
  const navigate = useNavigate();
  const [smtpServer, setSmtpServer] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [smtpSenderEmail, setSmtpSenderEmail] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const backendUrl = window.BACKEND_URL;

  const handleSave = async () => {
    setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  const handleTest = async () => {
    setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="settings-container" style={{
      padding: 'clamp(1rem, 3vw, 2rem)',
      maxWidth: '600px',
      width: '100%',
      margin: '0 auto',
      boxSizing: 'border-box'
    }}>
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 'clamp(1.5rem, 4vw, 2rem)',
        flexWrap: 'wrap',
        gap: 'clamp(0.5rem, 2vw, 1rem)'
      }}>
        <h1 style={{
          fontSize: 'clamp(1.5rem, 5vw, 2.5rem)',
          margin: 0,
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          flex: '1'
        }}>
          Configuration SMTP
        </h1>
        <button 
          onClick={() => navigate('/')}
          style={{
            backgroundColor: 'var(--clr-surface-a20)',
            color: 'var(--clr-primary-a50)',
            padding: 'clamp(0.5rem, 2vw, 0.75rem) clamp(0.75rem, 3vw, 1.25rem)',
            fontSize: 'clamp(0.875rem, 2vw, 1rem)',
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
        >
          Retour
        </button>
      </div>

      {message && (
        <div style={{
          padding: 'clamp(0.75rem, 2vw, 1rem)',
          marginBottom: 'clamp(1.5rem, 4vw, 2rem)',
          borderRadius: '6px',
          backgroundColor: messageType === 'success' ? 'rgba(0, 255, 0, 0.1)' : 
                         messageType === 'error' ? 'rgba(255, 0, 0, 0.1)' : 
                         'rgba(0, 0, 255, 0.1)',
          color: messageType === 'success' ? '#4caf50' : 
                messageType === 'error' ? '#f44336' : 
                '#2196f3',
          border: `1px solid ${
            messageType === 'success' ? '#4caf50' : 
            messageType === 'error' ? '#f44336' : 
            '#2196f3'
          }`,
          fontSize: 'clamp(0.875rem, 2vw, 1rem)'
        }}>
          {message}
        </div>
      )}

      <div className="settings-form" style={{
        backgroundColor: 'var(--clr-surface-a10)',
        padding: 'clamp(1.5rem, 4vw, 2rem)',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <InputField 
          id="smtp-server"
          label="Serveur SMTP"
          value={smtpServer}
          onChange={(e) => setSmtpServer(e.target.value)}
          placeholder="ex: ssl0.ovh.net"
        />
        
        <InputField 
          id="smtp-port"
          label="Port SMTP"
          value={smtpPort}
          onChange={(e) => setSmtpPort(e.target.value)}
          placeholder="ex: 465"
        />
        
        <InputField 
          id="smtp-user"
          label="Utilisateur SMTP"
          value={smtpUser}
          onChange={(e) => setSmtpUser(e.target.value)}
          placeholder="ex: user@domain.com"
        />
        
        <InputField 
          id="smtp-password"
          label="Mot de passe SMTP"
          type="password"
          value={smtpPassword}
          onChange={(e) => setSmtpPassword(e.target.value)}
          placeholder="••••••••"
        />

        <InputField 
          id="smtp-sender"
          label="Email d'envoi"
          value={smtpSenderEmail}
          onChange={(e) => setSmtpSenderEmail(e.target.value)}
          placeholder="ex: no-reply@domain.com"
        />

        <div style={{
          display: 'flex',
          gap: 'clamp(0.5rem, 2vw, 1rem)',
          marginTop: 'clamp(1.5rem, 4vw, 2rem)',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={handleSave}
            disabled={isLoading}
            style={{
              flex: '1',
              minWidth: '120px',
              padding: 'clamp(0.75rem, 2vw, 1rem)',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)',
              backgroundColor: 'var(--clr-primary-a30)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isLoading ? 'wait' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'all 0.3s ease'
            }}
          >
            {isLoading ? 'Enregistrement...' : 'Enregistrer'}
          </button>

          <button
            onClick={handleTest}
            disabled={isLoading}
            style={{
              flex: '1',
              minWidth: '120px',
              padding: 'clamp(0.75rem, 2vw, 1rem)',
              fontSize: 'clamp(0.875rem, 2vw, 1rem)',
              backgroundColor: 'var(--clr-surface-a30)',
              color: 'var(--clr-primary-a50)',
              border: 'none',
              borderRadius: '6px',
              cursor: isLoading ? 'wait' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'all 0.3s ease'
            }}
          >
            {isLoading ? 'Test en cours...' : 'Tester'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SMTPSettings;

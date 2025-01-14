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
  const [isLoading, setIsLoading] = useState(false);

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

  const InputField = ({ label, type = "text", value, onChange, placeholder }) => (
    <div className="form-group" style={{
      marginBottom: '1.5rem',
    }}>
      <label style={{
        display: 'block',
        marginBottom: '0.5rem',
        color: 'var(--clr-primary-a40)',
        fontSize: '0.9rem'
      }}>
        {label}
      </label>
      <input 
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: 'var(--clr-surface-a20)',
          color: 'var(--clr-primary-a50)',
          border: '1px solid var(--clr-surface-a30)',
          borderRadius: '6px',
          fontSize: '1rem',
          transition: 'all 0.3s ease'
        }}
      />
    </div>
  );

  return (
    <div className="settings-container" style={{
      padding: '2rem',
      maxWidth: '600px',
      width: '100%',
      margin: '0 auto'
    }}>
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          margin: 0,
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Configuration SMTP
        </h1>
        <button 
          onClick={() => navigate('/')}
          style={{
            backgroundColor: 'var(--clr-surface-a20)',
            color: 'var(--clr-primary-a50)',
            transition: 'all 0.3s ease'
          }}
        >
          Retour
        </button>
      </div>

      {message && (
        <div style={{
          padding: '1rem',
          marginBottom: '2rem',
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
          }`
        }}>
          {message}
        </div>
      )}

      <div className="settings-form" style={{
        backgroundColor: 'var(--clr-surface-a10)',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <InputField 
          label="Serveur SMTP"
          value={smtpServer}
          onChange={(e) => setSmtpServer(e.target.value)}
          placeholder="ex: ssl0.ovh.net"
        />
        
        <InputField 
          label="Port SMTP"
          value={smtpPort}
          onChange={(e) => setSmtpPort(e.target.value)}
          placeholder="ex: 465"
        />
        
        <InputField 
          label="Utilisateur SMTP"
          value={smtpUser}
          onChange={(e) => setSmtpUser(e.target.value)}
          placeholder="Votre nom d'utilisateur"
        />
        
        <InputField 
          label="Mot de passe SMTP"
          type="password"
          value={smtpPassword}
          onChange={(e) => setSmtpPassword(e.target.value)}
          placeholder="Votre mot de passe"
        />
        
        <InputField 
          label="Email d'envoi"
          type="email"
          value={smtpSenderEmail}
          onChange={(e) => setSmtpSenderEmail(e.target.value)}
          placeholder="email@exemple.com"
        />

        <div className="button-group" style={{
          display: 'flex',
          gap: '1rem',
          marginTop: '2rem'
        }}>
          <button 
            onClick={handleSave}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '1rem',
              fontSize: '1.1rem',
              backgroundColor: 'var(--clr-primary-a30)',
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
              flex: 1,
              padding: '1rem',
              fontSize: '1.1rem',
              backgroundColor: 'var(--clr-surface-a30)',
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

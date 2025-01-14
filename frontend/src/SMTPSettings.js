import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: 'var(--clr-surface-a10)',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px'
  },
  formGroup: {
    width: '100%',
    marginBottom: '15px'
  },
  label: {
    display: 'block',
    marginBottom: '5px',
    color: 'var(--clr-primary-a50)',
    fontWeight: 'bold'
  },
  input: {
    width: '100%',
    padding: '8px',
    backgroundColor: 'var(--clr-surface-a20)',
    border: '1px solid var(--clr-surface-a30)',
    borderRadius: '4px',
    color: 'var(--clr-primary-a50)'
  },
  buttonGroup: {
    display: 'flex',
    gap: '10px',
    marginTop: '20px'
  },
  button: {
    padding: '10px 20px',
    backgroundColor: 'var(--clr-primary-a30)',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'background-color 0.3s'
  },
  secondaryButton: {
    backgroundColor: 'var(--clr-surface-a20)',
    color: 'var(--clr-primary-a50)'
  },
  message: {
    padding: '10px',
    marginBottom: '20px',
    borderRadius: '4px',
    width: '100%'
  },
  successMessage: {
    backgroundColor: 'var(--clr-success-a10)',
    color: 'var(--clr-success-a50)',
    border: '1px solid var(--clr-success-a20)'
  },
  errorMessage: {
    backgroundColor: 'var(--clr-error-a10)',
    color: 'var(--clr-error-a50)',
    border: '1px solid var(--clr-error-a20)'
  },
  infoMessage: {
    backgroundColor: 'var(--clr-info-a10)',
    color: 'var(--clr-info-a50)',
    border: '1px solid var(--clr-info-a20)'
  }
};

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

  const getMessageStyle = () => {
    switch (messageType) {
      case 'success':
        return { ...styles.message, ...styles.successMessage };
      case 'error':
        return { ...styles.message, ...styles.errorMessage };
      case 'info':
        return { ...styles.message, ...styles.infoMessage };
      default:
        return styles.message;
    }
  };

  return (
    <div style={styles.container}>
      <h1>Configuration SMTP</h1>
      
      <div style={styles.content}>
        {message && (
          <div style={getMessageStyle()}>
            {message}
          </div>
        )}

        <div style={styles.formGroup}>
          <label style={styles.label}>Serveur SMTP:</label>
          <input 
            type="text" 
            value={smtpServer} 
            onChange={(e) => setSmtpServer(e.target.value)}
            placeholder="ex: ssl0.ovh.net"
            style={styles.input}
            name="smtpServer"
            autoComplete="off"
          />
        </div>
        
        <div style={styles.formGroup}>
          <label style={styles.label}>Port SMTP:</label>
          <input 
            type="text" 
            value={smtpPort} 
            onChange={(e) => setSmtpPort(e.target.value)}
            placeholder="ex: 465"
            style={styles.input}
          />
        </div>
        
        <div style={styles.formGroup}>
          <label style={styles.label}>Utilisateur SMTP:</label>
          <input 
            type="text" 
            value={smtpUser} 
            onChange={(e) => setSmtpUser(e.target.value)}
            placeholder="ex: user@domain.com"
            style={styles.input}
            name="smtpUser"
            autoComplete="username"
          />
        </div>
        
        <div style={styles.formGroup}>
          <label style={styles.label}>Mot de passe SMTP:</label>
          <input 
            type="password" 
            value={smtpPassword} 
            onChange={(e) => setSmtpPassword(e.target.value)}
            placeholder="Votre mot de passe SMTP"
            style={styles.input}
            name="smtpPassword"
            autoComplete="current-password"
          />
        </div>
        
        <div style={styles.formGroup}>
          <label style={styles.label}>Email de l'expéditeur:</label>
          <input 
            type="email" 
            value={smtpSenderEmail} 
            onChange={(e) => setSmtpSenderEmail(e.target.value)}
            placeholder="ex: no-reply@domain.com"
            style={styles.input}
            name="smtpSenderEmail"
            autoComplete="email"
          />
        </div>

        <div style={styles.buttonGroup}>
          <button onClick={handleSave} style={styles.button}>
            Enregistrer
          </button>
          <button 
            onClick={handleTest} 
            style={{...styles.button, ...styles.secondaryButton}}
          >
            Tester la configuration
          </button>
          <button 
            onClick={() => navigate('/')} 
            style={{...styles.button, ...styles.secondaryButton}}
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    </div>
  );
};

export default SMTPSettings;

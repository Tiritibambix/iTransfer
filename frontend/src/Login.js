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
  button: {
    width: '100%',
    padding: '10px 20px',
    backgroundColor: 'var(--clr-primary-a30)',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'background-color 0.3s'
  },
  errorMessage: {
    padding: '10px',
    marginBottom: '20px',
    borderRadius: '4px',
    width: '100%',
    backgroundColor: 'var(--clr-error-a10)',
    color: 'var(--clr-error-a50)',
    border: '1px solid var(--clr-error-a20)'
  }
};

const Login = ({ backendUrl }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`${backendUrl}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.status === 200) {
        const data = await response.json();
        localStorage.setItem('authToken', data.token);
        navigate('/');
      } else {
        setError('Identifiants invalides.');
      }
    } catch (error) {
      setError('Erreur réseau ou backend.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <h1>Connexion</h1>
        
        {error && (
          <div style={styles.errorMessage}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div style={styles.formGroup}>
            <label style={styles.label}>
              Nom d'utilisateur:
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              required
              name="username"
              autoComplete="username"
              placeholder="Votre nom d'utilisateur"
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>
              Mot de passe:
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
              name="password"
              autoComplete="current-password"
              placeholder="Votre mot de passe"
            />
          </div>

          <button 
            type="submit" 
            style={styles.button}
          >
            Se connecter
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;

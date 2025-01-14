import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = ({ backendUrl }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLoading) return;
    
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.status === 200) {
        const data = await response.json();
        localStorage.setItem('authToken', data.token);
        navigate('/');
      } else {
        setError('Identifiants invalides');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '1rem'
    }}>
      <div style={{
        width: '90%',
        maxWidth: '320px',
        backgroundColor: 'var(--clr-surface-a10)',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{
          fontSize: '2rem',
          marginBottom: '1.5rem',
          textAlign: 'center',
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          iTransfer
        </h1>

        <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Nom d'utilisateur"
              value={username}
              onChange={e => setUsername(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: 'var(--clr-surface-a20)',
                color: 'var(--clr-primary-a50)',
                border: '1px solid var(--clr-surface-a30)',
                borderRadius: '6px',
                fontSize: '0.9rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <input
              type="password"
              placeholder="Mot de passe"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: 'var(--clr-surface-a20)',
                color: 'var(--clr-primary-a50)',
                border: '1px solid var(--clr-surface-a30)',
                borderRadius: '6px',
                fontSize: '0.9rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              backgroundColor: 'var(--clr-primary-a30)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isLoading ? 'wait' : 'pointer',
              opacity: isLoading ? 0.7 : 1
            }}
          >
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        {error && (
          <div style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(255, 0, 0, 0.1)',
            color: '#f44336',
            border: '1px solid #f44336',
            borderRadius: '6px',
            textAlign: 'center',
            fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;

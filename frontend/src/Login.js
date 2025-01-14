import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = ({ backendUrl }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault(); // Empêcher le rechargement de la page
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

  const InputField = ({ type, placeholder, value, onChange }) => (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      style={{
        width: '100%',
        padding: '12px',
        marginBottom: '1rem',
        backgroundColor: 'var(--clr-surface-a20)',
        color: 'var(--clr-primary-a50)',
        border: '1px solid var(--clr-surface-a30)',
        borderRadius: '6px',
        fontSize: '1rem',
        transition: 'all 0.3s ease',
        outline: 'none'
      }}
    />
  );

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        backgroundColor: 'var(--clr-surface-a10)',
        padding: '2.5rem',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '2rem',
          textAlign: 'center',
          background: 'linear-gradient(45deg, var(--clr-primary-a40), var(--clr-primary-a30))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          iTransfer
        </h1>

        <form onSubmit={handleLogin} style={{ marginBottom: '1.5rem' }}>
          <InputField
            type="text"
            placeholder="Nom d'utilisateur"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <InputField
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '1rem',
              fontSize: '1.1rem',
              backgroundColor: 'var(--clr-primary-a30)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              opacity: isLoading ? 0.7 : 1,
              marginTop: '1rem'
            }}
          >
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        {error && (
          <div style={{
            padding: '1rem',
            backgroundColor: 'rgba(255, 0, 0, 0.1)',
            color: '#f44336',
            border: '1px solid #f44336',
            borderRadius: '6px',
            textAlign: 'center',
            fontSize: '0.9rem'
          }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;

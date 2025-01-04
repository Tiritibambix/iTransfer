import React, { useState } from 'react';

const SMTPSettings = () => {
  const [smtpServer, setSmtpServer] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');

  const handleSave = () => {
    // Logique pour enregistrer les paramètres SMTP
    console.log({ smtpServer, smtpPort, smtpUser, smtpPassword });
  };

  return (
    <div>
      <h1>Configuration SMTP</h1>
      <div>
        <label>Serveur SMTP:</label>
        <input type="text" className="btn" value={smtpServer} onChange={(e) => setSmtpServer(e.target.value)} />
      </div>
      <div>
        <label>Port SMTP:</label>
        <input type="text" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} />
      </div>
      <div>
        <label>Utilisateur SMTP:</label>
        <input type="text" value={smtpUser} onChange={(e) => setSmtpUser(e.target.value)} />
      </div>
      <div>
        <label>Mot de passe SMTP:</label>
        <input type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)} />
      </div>
      <button onClick={handleSave}>Enregistrer</button>
      <button className="btn" onClick={() => window.location.href = '/upload'}>Retour à l'upload</button>
      <button className="btn" onClick={() => window.location.href = '/upload'}>Retour à l'upload</button>
    </div>
  );
};

export default SMTPSettings;

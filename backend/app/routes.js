const express = require('express');
const fs = require('fs');
const path = require('path');

const router = express.Router();

// Route pour enregistrer les paramètres SMTP
router.post('/api/save-smtp-settings', (req, res) => {
  const { smtpServer, smtpPort, smtpUser, smtpPassword, smtpSenderEmail } = req.body;
  const configPath = path.join(__dirname, 'smtpConfig.json');

  const config = {
    smtpServer,
    smtpPort,
    smtpUser,
    smtpPassword,
    smtpSenderEmail,
  };

  fs.writeFile(configPath, JSON.stringify(config, null, 2), (err) => {
    if (err) {
      return res.status(500).send('Erreur lors de l\'enregistrement des paramètres SMTP');
    }
    res.status(200).send('Paramètres SMTP enregistrés avec succès');
  });
});

module.exports = router;

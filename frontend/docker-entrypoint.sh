#!/bin/sh

# Création du fichier de configuration avec les variables d'environnement
echo "window.APP_CONFIG = {
  backendUrl: '${BACKEND_URL}'
};" > /usr/share/nginx/html/config.js

# Démarrage de nginx
exec nginx -g 'daemon off;'

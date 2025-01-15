#!/bin/sh

# Remplacer la configuration dans le HTML
sed -i "s|window.BACKEND_URL = '.*'|window.BACKEND_URL = '${BACKEND_URL}'|g" /usr/share/nginx/html/index.html

# Démarrer nginx
nginx -g 'daemon off;'

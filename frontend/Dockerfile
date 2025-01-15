# Étape 1 : Construction de l'application
FROM node:14 AS builder

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration pour npm
COPY frontend/package.json frontend/package-lock.json* ./

# Installer les dépendances
RUN npm install

# Copier tout le code source du frontend
COPY frontend/ .

# Construire l'application
RUN npm run build

# Étape 2 : Servir avec Nginx
FROM nginx:alpine

# Copier les fichiers construits depuis l'étape de build
COPY --from=builder /app/build /usr/share/nginx/html

# Créer le script d'entrypoint personnalisé
RUN echo '#!/bin/sh\n\
# Remplacer la configuration dans le HTML\n\
sed -i "s|window.BACKEND_URL = .*|window.BACKEND_URL = '\''$BACKEND_URL'\''|g" /usr/share/nginx/html/index.html\n\
\n\
# Démarrer nginx\n\
exec nginx -g '\''daemon off;'\''\n\
' > /docker-entrypoint.sh \
&& chmod +x /docker-entrypoint.sh

# Configuration Nginx pour SPA
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri /index.html; \
    } \
    error_page 404 /index.html; \
}' > /etc/nginx/conf.d/default.conf

# Exposer le port utilisé par Nginx
EXPOSE 80

# Utiliser notre script comme point d'entrée
ENTRYPOINT ["/docker-entrypoint.sh"]

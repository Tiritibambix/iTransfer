# Étape 1 : Construction de l'application
FROM node:14 AS builder

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration pour npm
COPY frontend/package.json frontend/package-lock.json* ./

# Installer les dépendances
RUN npm install

# Mettre à jour Babel pour éviter les conflits de version
RUN npm install --save-dev @babel/core@latest

# Copier tout le code source du frontend
COPY frontend/ .

# Construire l'application
RUN npm run build

# Étape 2 : Servir avec Nginx
FROM nginx:alpine

# Copier les fichiers construits depuis l'étape de build
COPY --from=builder /app/build /usr/share/nginx/html

# Créer le script d'entrypoint personnalisé
RUN printf '#!/bin/sh\n\
echo "BACKEND_URL=$BACKEND_URL"\n\
echo "Content before replacement:"\n\
cat /usr/share/nginx/html/index.html\n\
sed -i "s|TO_BE_REPLACED_BY_ENTRYPOINT|$BACKEND_URL|g" /usr/share/nginx/html/index.html\n\
echo "Content after replacement:"\n\
cat /usr/share/nginx/html/index.html\n\
exec nginx -g "daemon off;"\n' > /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Configuration Nginx pour SPA
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri /index.html;\n\
    }\n\
    error_page 404 /index.html;\n\
}\n' > /etc/nginx/conf.d/default.conf

# Exposer le port utilisé par Nginx
EXPOSE 80

# Utiliser notre script comme point d'entrée
ENTRYPOINT ["/docker-entrypoint.sh"]

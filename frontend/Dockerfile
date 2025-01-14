# Étape 1 : Construction de l'application
FROM node:14 AS builder

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration pour npm
COPY frontend/package*.json ./

# Installer les dépendances (incluant @babel/plugin-proposal-private-property-in-object)
RUN npm install && npm audit fix

# Copier tout le code source du frontend
COPY frontend/ .

# Construire l'application
RUN npm run build

# Étape 2 : Servir avec Nginx
FROM nginx:alpine

# Copier les fichiers construits depuis l'étape de build
COPY --from=builder /app/build /usr/share/nginx/html

# Copier le script d'entrée
COPY frontend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

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
CMD ["nginx", "-g", "daemon off;"]

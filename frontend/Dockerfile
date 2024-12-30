# Étape 1 : Construction de l'application
FROM node:14 AS builder

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration pour npm
COPY frontend/package*.json ./

# Vérifier que les fichiers sont copiés correctement
RUN ls -la

# Installer les dépendances
RUN npm install

# Copier tout le code source du frontend
COPY frontend/ .

# Construire l'application
RUN npm run build

# Vérifier les fichiers générés
RUN ls -la build

# Étape 2 : Servir avec Nginx
FROM nginx:alpine

# Copier les fichiers construits depuis l'étape de build
COPY --from=builder /app/build /usr/share/nginx/html

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

# Commande pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]

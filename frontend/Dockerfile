# Étape 1 : Construction de l'application
FROM node:16-alpine AS builder

# Définir le répertoire de travail
WORKDIR /app

# Ajouter les arguments de build
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

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

# Copier la configuration Nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port utilisé par Nginx
EXPOSE 80

# Commande pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]

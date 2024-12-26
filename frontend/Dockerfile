# Dockerfile - Frontend
FROM node:16-buster

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le reste de l'application
COPY . .

# Build de l'application React
RUN npm run build

# Exposer le port utilisé par React (via nginx ou autre)
EXPOSE 3000

# Commande pour démarrer
CMD ["npm", "start"]

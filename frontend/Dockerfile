FROM node:14

WORKDIR /app

# Copier package.json et package-lock.json depuis le dossier frontend
COPY frontend/package*.json ./

# Installer les dépendances
RUN npm install

# Copier le reste de l'application depuis le dossier frontend
COPY frontend/ .

# Construire l'application
RUN npm run build

# Installer serve pour servir l'application
RUN npm install -g serve

# Exposer le port sur lequel l'application sera servie
EXPOSE 3000

# Commande pour démarrer l'application
CMD ["serve", "-s", "build"]

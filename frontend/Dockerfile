# Utiliser une image de base officielle Node.js
FROM node:14

# Définir le répertoire de travail
WORKDIR /app

# Copier package.json et package-lock.json
COPY frontend/package*.json ./

# Installer les dépendances
RUN npm install

# Copier le reste des fichiers de l'application
COPY frontend/ .

# Vérifier les fichiers copiés
RUN ls -la
RUN ls -la src

# Construire l'application
RUN npm run build

# Installer serve pour servir l'application
RUN npm install -g serve

# Exposer le port sur lequel l'application sera accessible
EXPOSE 3000

# Commande pour démarrer l'application
CMD ["serve", "-s", "build"]

# Utiliser une image de base officielle Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY backend/ .

# Vérifier les fichiers copiés
RUN ls -la

# Installer les dépendances
RUN pip install -r requirements.txt

# Exposer le port sur lequel l'application sera accessible
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "app.py"]

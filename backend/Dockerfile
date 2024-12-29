# Utiliser une image de base officielle Python
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier requirements.txt depuis la racine du dépôt
COPY /requirements.txt /app/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le reste des fichiers de l'application
COPY backend/app /app

# Vérifier les fichiers copiés
RUN ls -la /app

# Exposer le port sur lequel l'application sera accessible
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "app.py"]

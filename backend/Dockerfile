# Utiliser une image de base officielle Python
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt /app/requirements.txt

# Installer les dépendances et vérifier leur compatibilité
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip check

# Copier le reste des fichiers de l'application
COPY backend/app /app

# Vérifier les fichiers copiés (facultatif mais utile pour debug)
RUN ls -la /app

# Exposer le port sur lequel l'application sera accessible
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "app.py"]

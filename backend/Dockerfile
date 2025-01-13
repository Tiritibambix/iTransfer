# Utiliser une image Python légère
FROM python:3.10-slim

# Installer les bibliothèques nécessaires pour mysqlclient et autres dépendances
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer pip-check et PyYAML
RUN pip install --upgrade pip pip-check PyYAML

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY /backend/requirements.txt /app/requirements.txt

# Installer les dépendances et vérifier la compatibilité
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip-check

# Créer les dossiers nécessaires
RUN mkdir -p /app/uploads /app/data && chmod -R 777 /app/uploads /app/data

# Copier le docker-compose.yml pour la lecture des ports
COPY docker-compose.yml /app/docker-compose.yml

# Copier le code de l'application
COPY /backend/app /app/app
COPY /backend/wsgi.py /app/wsgi.py

# Exposer le port de l'application
EXPOSE 5000

# Définir les variables d'environnement
ENV FLASK_APP=wsgi.py
ENV PYTHONPATH=/app

# Commande pour démarrer l'application
CMD ["python", "wsgi.py"]

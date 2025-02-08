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

# Installer pip-check
RUN pip install --upgrade pip pip-check

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt /app/requirements.txt

# Installer les dépendances et vérifier la compatibilité
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip-check

# Créer les dossiers nécessaires
RUN mkdir -p /app/uploads /app/data /app/logs && \
    chmod -R 777 /app/uploads /app/data /app/logs

# Copier le code de l'application
COPY backend /app/

# Exposer le port
EXPOSE 5000

# Variables d'environnement pour Gunicorn
ENV PYTHONUNBUFFERED=1

# Commande pour démarrer l'application avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]

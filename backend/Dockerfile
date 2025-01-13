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

# Copier le code de l'application
COPY backend /app/

# Créer le dossier data et lui donner les permissions nécessaires
RUN mkdir -p /app/data && chmod -R 777 /app/data

# Exposer le port
EXPOSE 5000

# Définir la commande de démarrage
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]

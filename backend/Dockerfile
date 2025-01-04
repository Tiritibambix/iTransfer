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

# Créer le dossier uploads et lui donner les permissions nécessaires
RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads


# Copier le code de l'application
COPY /backend/app /app/app
COPY /backend/run.py /app/run.py

# Copier le script d'entrée
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "run.py"]

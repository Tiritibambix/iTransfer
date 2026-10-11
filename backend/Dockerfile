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

# Commande pour démarrer l'application avec Gunicorn.
#
# Tuned for massive uploads/downloads:
# - gthread workers: for non-sync workers Gunicorn's --timeout is a heartbeat
#   liveness check (a background thread keeps notifying the arbiter), NOT a
#   per-request cap. A multi-GB upload taking many minutes is therefore never
#   killed mid-transfer. With the previous sync workers the default 30s timeout
#   was a hard per-request limit, which is exactly what dropped large uploads.
# - --timeout is still set generously as a safety net for the CPU-bound
#   zip/hash step that runs after the body is received.
# - All knobs are env-overridable at `docker run` / compose time, no rebuild.
# sh -c + exec so Gunicorn stays PID 1 and receives SIGTERM for graceful stop.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5000 --worker-class gthread --workers ${GUNICORN_WORKERS:-4} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-1800} --graceful-timeout 30 --access-logfile - --error-logfile - app:app"]

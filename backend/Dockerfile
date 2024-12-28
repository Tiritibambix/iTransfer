FROM python:3.9-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    python3-dev \
    default-libmysqlclient-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier le fichier requirements.txt d'abord pour tirer parti du cache Docker
COPY app/requirements.txt ./

# Mettre à jour pip et installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt > pip_install_log.txt 2>&1 || (cat pip_install_log.txt && exit 1)

# Copier le reste de l'application
COPY app /app

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]

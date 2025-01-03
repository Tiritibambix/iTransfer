# Utiliser une image de base officielle Python
FROM python:3.10-slim

# Installer les bibliothèques nécessaires pour mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc \
    && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip check

# Copier le code de l'application
COPY /backend/app /app

# Vérifier les fichiers copiés (optionnel pour debug)
RUN ls -la /app

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "app.py"]

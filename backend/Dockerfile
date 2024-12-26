# Dockerfile - Backend
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Exposer le port utilisé par Flask
EXPOSE 5000

# Commande pour lancer l'application
CMD ["python", "app.py"]

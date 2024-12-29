# Dockerfile dans le dossier ./backend
FROM python:3.10-slim

WORKDIR /app

# Copier le fichier requirements.txt depuis le bon chemin
COPY app/requirements.txt /app/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier tout le contenu de backend/app
COPY app /app

EXPOSE 5000

CMD ["python", "app.py"]

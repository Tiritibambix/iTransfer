# Dockerfile dans ./backend
FROM python:3.10-slim

WORKDIR /app

# Copier requirements.txt depuis la racine du dépôt
COPY ../../requirements.txt /app/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le dossier app depuis backend
COPY ./app /app

EXPOSE 5000

CMD ["python", "app.py"]

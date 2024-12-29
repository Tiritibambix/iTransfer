# Utilisation d'une image Python légère
FROM python:3.10-slim

WORKDIR /app

# Copier le fichier requirements.txt depuis la racine
COPY /requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le contenu entier du dossier backend/app
COPY ./app /app

EXPOSE 5000

CMD ["python", "app.py"]

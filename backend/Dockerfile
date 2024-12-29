# Utilisation de la dernière version LTS de Python
FROM python:3.10-slim as base

# Étape de construction pour installer uniquement les dépendances nécessaires
FROM base as builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Étape finale pour exécuter l'application
FROM base
WORKDIR /app
COPY --from=builder /root/.cache /root/.cache
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]

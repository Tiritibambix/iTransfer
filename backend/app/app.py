from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Configurer CORS pour permettre toutes les origines
CORS(app, supports_credentials=True)

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    # Récupérer l'URL du frontend dynamiquement pour chaque requête
    frontend_url = request.headers.get('Origin', 'http://localhost:3500')  # Si pas d'Origin, fallback à localhost:3500

    if request.method == 'OPTIONS':  # Gérer la pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé")

        # Vérifier si le dossier uploads existe, sinon le créer
        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Sauvegarde du fichier
        upload_path = os.path.join(upload_dir, file.filename)
        file.save(upload_path)

        response = jsonify({"message": f"Fichier {file.filename} reçu avec succès"})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 201
    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Vérifie les identifiants fournis par le client et gère les requêtes CORS.
    """
    frontend_url = request.headers.get('Origin', 'http://localhost:3500')  # Dynamique

    if request.method == 'OPTIONS':  # Pré-requête CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    # Gestion de la méthode POST
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        token = "fake_jwt_token_for_demo_purposes"
        response = jsonify({"message": "Login réussi", "token": token})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 200
    else:
        response = jsonify({"error": "Identifiants invalides."})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Ecouter sur toutes les interfaces réseau
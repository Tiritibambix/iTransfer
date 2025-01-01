from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)

# Récupérer l'URL du frontend dynamiquement
frontend_url = request.headers.get('Origin')

# Si l'URL du frontend n'est pas définie, on utilise localhost:3500 par défaut
if not frontend_url:
    frontend_url = 'http://localhost:3500'

# Configurer CORS pour permettre toutes les requêtes provenant de l'URL dynamique
CORS(app, resources={r"/upload": {"origins": frontend_url}}, supports_credentials=True)

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
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

        # Sauvegarde du fichier
        upload_path = '/app/uploads/' + file.filename
        file.save(upload_path)

        response = jsonify({"message": f"Fichier {file.filename} reçu avec succès"})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 201
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Ecouter sur toutes les interfaces réseau

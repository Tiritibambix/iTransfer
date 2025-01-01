from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

# Charger l'URL du frontend depuis les variables d'environnement
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3500')

# Configurer les logs
logging.basicConfig(level=logging.INFO)

# Activer CORS pour autoriser uniquement l'origine définie
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':  # Pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", FRONTEND_URL)
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé")

        # Sauvegarder le fichier
        upload_path = os.path.join('/app/uploads', file.filename)
        file.save(upload_path)

        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500)  # Utiliser le port 5500

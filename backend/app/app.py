from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)

# Dynamiser l'URL du frontend à partir de l'environnement ou utiliser localhost si absent
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3500')

# Configurer CORS pour autoriser les requêtes provenant du frontend
CORS(app, resources={r"/upload": {"origins": FRONTEND_URL}})

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':  # Gérer la pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", FRONTEND_URL)
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

        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Flask écoute sur toutes les interfaces réseau disponibles (0.0.0.0)
    app.run(host='0.0.0.0', port=5000)

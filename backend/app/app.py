from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

# Charger les variables d'environnement injectées par Docker Compose
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3500')

# Configurer CORS pour autoriser le frontend
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

# Configurer les logs
logging.basicConfig(level=logging.INFO)

# Configurer le dossier d'uploads
UPLOAD_FOLDER = '/app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        file = request.files['file']
        if not file:
            raise ValueError("Aucun fichier envoyé")

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        logging.info(f"Fichier {file.filename} sauvegardé avec succès à {file_path}")
        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

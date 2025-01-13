from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import Config
import os
import socket

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Activer CORS
CORS(app, supports_credentials=True)

def get_host_ip():
    try:
        # Créer une connexion socket vers un serveur externe (ne se connecte pas réellement)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# Définir l'URL du backend
host_ip = os.environ.get('HOST_IP') or get_host_ip()
app.config['BACKEND_URL'] = f"http://{host_ip}:5500"
app.logger.info(f"URL du backend configurée : {app.config['BACKEND_URL']}")

# Créer les tables au démarrage
with app.app_context():
    app.logger.info("Base de données initialisée avec succès")

@app.after_request
def add_cors_headers(response):
    """
    Ajouter les headers CORS à toutes les réponses.
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE, PATCH')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

    return response

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    try:
        if request.method == 'OPTIONS':  # Pré-demande CORS
            return jsonify({'message': 'CORS preflight success'}), 200

        # Récupérer le fichier de la requête
        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé.")

        # Log du fichier reçu pour debug
        app.logger.info(f"Nom du fichier reçu : {file.filename}")

        # Sauvegarder le fichier dans le dossier uploads
        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        upload_path = os.path.join(upload_dir, file.filename)
        file.save(upload_path)

        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

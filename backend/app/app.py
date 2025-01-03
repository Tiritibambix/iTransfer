from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Configuration de CORS
CORS(app, supports_credentials=True)

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    frontend_url = request.headers.get('Origin', 'http://localhost:3500')

    if request.method == 'OPTIONS':  # Pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    try:
        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé")

        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        upload_path = os.path.join(upload_dir, file.filename)
        file.save(upload_path)

        response = jsonify({"message": f"Fichier {file.filename} reçu avec succès"})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 201

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

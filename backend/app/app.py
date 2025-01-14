from flask import Flask, jsonify, request
from flask_cors import CORS
from . import app, db
from .config import Config
from .database import init_db
import os
from werkzeug.utils import secure_filename

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuration CORS centralisée
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # Initialiser la base de données
    init_db(app)
    
    # Créer les tables au démarrage
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Base de données initialisée avec succès")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
        
    return app

# Créer l'application
app = create_app()

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

        safe_filename = secure_filename(file.filename)
        upload_path = os.path.join(upload_dir, safe_filename)
        file.save(upload_path)

        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": "An internal error has occurred."}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify, request
from flask_cors import CORS
from . import app, db
from .config import Config
from .database import init_db
from .models import FileUpload
import os
import time
import threading
import schedule
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import exc

def wait_for_db(max_retries=5, delay=2):
    """Attend que la base de données soit disponible"""
    for attempt in range(max_retries):
        try:
            # Tente de se connecter à la base de données
            db.engine.connect()
            app.logger.info("Connexion à la base de données établie avec succès")
            return True
        except exc.OperationalError as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée. Nouvelle tentative dans {delay} secondes...")
                time.sleep(delay)
                delay *= 2  # Augmente le délai entre chaque tentative
            else:
                app.logger.error("Impossible de se connecter à la base de données après plusieurs tentatives")
                raise
    return False

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
    
    # Attendre que la base de données soit disponible
    with app.app_context():
        wait_for_db()
        try:
            db.create_all()
            app.logger.info("Base de données initialisée avec succès")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
    
    return app

# Créer l'application
app = create_app()

# Configuration du scheduler pour le nettoyage des fichiers expirés
def cleanup_expired_files():
    try:
        # Récupérer tous les fichiers expirés
        expired_files = FileUpload.query.filter(FileUpload.expires_at < datetime.now()).all()
        
        for file in expired_files:
            try:
                # Supprimer le fichier physique
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f"Fichier expiré supprimé: {file_path}")
                
                # Supprimer l'entrée de la base de données
                db.session.delete(file)
                app.logger.info(f"Entrée de base de données supprimée pour le fichier: {file.id}")
            except Exception as e:
                app.logger.error(f"Erreur lors de la suppression du fichier {file.id}: {str(e)}")
        
        db.session.commit()
        app.logger.info("Nettoyage des fichiers expirés terminé")
    except Exception as e:
        app.logger.error(f"Erreur lors du nettoyage des fichiers expirés: {str(e)}")

def run_scheduler():
    with app.app_context():
        schedule.every(12).hours.do(cleanup_expired_files)
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Attendre 1 heure

# Démarrer le scheduler dans un thread séparé
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

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

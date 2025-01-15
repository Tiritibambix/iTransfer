from flask import Flask, jsonify, request
from flask_cors import CORS
from . import app, db
from .config import Config
from .database import init_db
import os
import time
import logging
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
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
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

# Importer les routes après la création de l'application
from . import routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

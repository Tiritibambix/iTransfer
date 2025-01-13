from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import Config
import os
import socket
import yaml

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

def get_host_ip():
    """Détecte l'IP de la machine hôte"""
    try:
        # Créer une connexion socket vers un serveur externe (ne se connecte pas réellement)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Utiliser Google DNS comme point de référence
        s.connect(("8.8.8.8", 80))
        # Récupérer l'IP locale utilisée pour la connexion
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Erreur lors de la détection de l'IP : {e}")
        return "localhost"

def get_ports_from_compose():
    """Lit le docker-compose.yml pour obtenir les ports configurés"""
    try:
        # Le fichier docker-compose.yml est copié à la racine du conteneur
        compose_path = '/app/docker-compose.yml'
        
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
            
        # Extraire les ports externes
        backend_port = None
        frontend_port = None
        
        # Lire les ports du backend
        backend_ports = compose_config['services']['backend']['ports']
        for port_mapping in backend_ports:
            if isinstance(port_mapping, str):
                external, internal = port_mapping.split(':')
                backend_port = external.strip('"')
                break
                
        # Lire les ports du frontend
        frontend_ports = compose_config['services']['frontend']['ports']
        for port_mapping in frontend_ports:
            if isinstance(port_mapping, str):
                external, internal = port_mapping.split(':')
                frontend_port = external.strip('"')
                break
                
        return backend_port, frontend_port
    except Exception as e:
        print(f"Erreur lors de la lecture du docker-compose.yml : {e}")
        return '5500', '3500'  # Valeurs par défaut en cas d'erreur

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Activer CORS
    CORS(app, supports_credentials=True)
    
    # Initialiser SQLAlchemy avec l'application
    db.init_app(app)
    
    # Obtenir les ports depuis le docker-compose.yml
    backend_port, frontend_port = get_ports_from_compose()
    
    # Définir l'URL du backend avec le port externe lu depuis docker-compose
    host_ip = get_host_ip()
    app.config['BACKEND_URL'] = f"http://{host_ip}:{backend_port}"
    app.config['FRONTEND_URL'] = f"http://{host_ip}:{frontend_port}"
    
    print(f"URL du backend configurée : {app.config['BACKEND_URL']}")
    print(f"URL du frontend configurée : {app.config['FRONTEND_URL']}")
    
    # Importer et enregistrer les routes
    from . import routes
    app.register_blueprint(routes.bp)
    
    # Créer les tables au démarrage avec gestion des erreurs
    max_retries = 5
    retry_delay = 5  # secondes
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("Base de données initialisée avec succès")
                break
        except Exception as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"Tentative {attempt + 1}/{max_retries} de connexion à la base de données échouée: {e}")
                import time
                time.sleep(retry_delay)
            else:
                app.logger.error(f"Impossible de se connecter à la base de données après {max_retries} tentatives: {e}")
                raise
    
    # Ajouter les headers CORS à toutes les réponses.
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE, PATCH')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

        return response

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

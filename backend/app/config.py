import os
import secrets
from sqlalchemy import create_engine

class Config:
    # Configuration de la base de données avec retry
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Vérifie la connexion avant utilisation
        'pool_recycle': 3600,   # Recycle les connexions après 1 heure
        'pool_timeout': 30,     # Timeout de 30 secondes pour obtenir une connexion
        'pool_size': 10,        # Taille du pool de connexions
        'max_overflow': 20      # Nombre maximum de connexions supplémentaires
    }
    
    # Génération d'une clé secrète aléatoire si non définie
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Configuration SMTP avec valeurs par défaut sécurisées
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # Configuration du fuseau horaire (requis)
    TIMEZONE = os.environ.get('TIMEZONE')
    
    # Configuration des chemins
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 * 1024  # 50 GB max-limit
    
    # Configuration admin avec valeurs par défaut sécurisées
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # Configuration SMTP
    SMTP_CONFIG_PATH = os.environ.get('SMTP_CONFIG_PATH') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'smtp_config.json')
    
    # Configuration de l'environnement
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')  # 'development' ou 'production'
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'  # Force HTTPS en production
    
    # Configuration du proxy
    PROXY_COUNT = int(os.environ.get('PROXY_COUNT', '1'))  # Nombre de proxies devant l'application
    PREFERRED_URL_SCHEME = 'https' if FORCE_HTTPS else 'http'
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Créer les dossiers nécessaires
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.SMTP_CONFIG_PATH), exist_ok=True)

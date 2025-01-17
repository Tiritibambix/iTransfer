import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Créer le dossier logs s'il n'existe pas
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configurer le logging au niveau racine
logging.basicConfig(level=logging.INFO)

# Configurer le logging
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

# Logger pour le fichier
file_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'itransfer.log'),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Logger pour la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Créer l'application Flask
app = Flask(__name__)
app.config.from_object('app.config.Config')

# Configurer le logger de l'application
app.logger.handlers.clear()  # Supprimer les handlers existants
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)
app.logger.propagate = True  # S'assurer que les logs sont propagés
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = []  # Supprimer les handlers par défaut de Werkzeug
werkzeug_logger.addHandler(file_handler)
werkzeug_logger.addHandler(console_handler)
werkzeug_logger.setLevel(logging.INFO)

app.logger.info('=== DÉMARRAGE DU BACKEND ITRANSFER ===')

# Initialiser les extensions
db = SQLAlchemy(app)
CORS(app, supports_credentials=True)

from app import routes

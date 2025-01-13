from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

# Initialiser les extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_object=None):
    app = Flask(__name__)
    
    # Configuration
    if config_object is None:
        from .config import Config
        config_object = Config
    
    app.config.from_object(config_object)
    
    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, supports_credentials=True)
    
    # Créer les tables au démarrage
    with app.app_context():
        db.create_all()
        app.logger.info("Base de données initialisée avec succès")
    
    # Importer et enregistrer les routes
    from . import routes
    
    return app

# Créer l'application
app = create_app()

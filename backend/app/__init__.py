from flask import Flask
from flask_cors import CORS
from .config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)  # Ajouter cette ligne pour activer CORS
app.config.from_object(Config)
db = SQLAlchemy(app)

from app import routes

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('app.config.Config')

# Initialiser les extensions
db = SQLAlchemy(app)
CORS(app, supports_credentials=True)

from app import routes

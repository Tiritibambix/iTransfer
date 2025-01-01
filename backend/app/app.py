from flask import Flask, jsonify, request, redirect, url_for, render_template
from flask_cors import CORS
import os

app = Flask(__name__)

# Identifiants administrateur (utiliser des variables d'environnement pour les valeurs sensibles)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpassword')

# CORS initialisé sans frontend_url, car il est dynamique
CORS(app, supports_credentials=True)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return redirect(url_for('upload'))
        else:
            return jsonify({"error": "Nom d'utilisateur ou mot de passe incorrect"}), 401
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return render_template('upload.html')  # Affiche la page d'upload après une connexion réussie

@app.route('/upload', methods=['POST'])
def upload_file():
    # Récupérer dynamiquement l'URL du frontend à chaque requête
    frontend_url = request.headers.get('Origin')
    if not frontend_url:
        frontend_url = 'http://localhost:3500'

    # Configurer CORS pour chaque requête
    CORS(app, resources={r"/upload": {"origins": frontend_url}}, supports_credentials=True)

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "Aucun fichier envoyé"}), 400

        upload_path = '/app/uploads/' + file.filename
        file.save(upload_path)
        
        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    return jsonify({"error": "Méthode non autorisée"}), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

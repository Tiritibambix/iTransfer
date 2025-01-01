from flask import Flask, jsonify, request, redirect, url_for, render_template, session
from flask_cors import CORS
import os

app = Flask(__name__)

# Secret key pour la gestion des sessions
app.secret_key = os.urandom(24)

# Identifiants administrateur (utiliser des variables d'environnement pour les valeurs sensibles)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpassword')

# CORS initialisé sans frontend_url, car il est dynamique
CORS(app, supports_credentials=True)

# Route pour la page d'index, redirige vers la page de login si l'utilisateur n'est pas connecté
@app.route('/')
def index():
    # Si l'utilisateur est déjà connecté, il est redirigé vers la page d'upload
    if 'authenticated' in session and session['authenticated']:
        return redirect(url_for('upload'))
    # Sinon, redirige vers la page de login
    return redirect(url_for('login')) 

# Route pour le login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Vérifie les identifiants
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['authenticated'] = True  # Stocke l'authentification dans la session
            return redirect(url_for('upload'))  # Redirige vers la page d'upload
        else:
            return jsonify({"error": "Nom d'utilisateur ou mot de passe incorrect"}), 401
    
    return render_template('login.html')  # Affiche le formulaire de login

# Page d'upload - nécessite une authentification
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Vérifie si l'utilisateur est authentifié
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('login'))  # Si non authentifié, redirige vers la page de login
    
    # Retourne la page d'upload
    return render_template('upload.html')

# Route de déconnexion
@app.route('/logout')
def logout():
    session.pop('authenticated', None)  # Efface la session d'authentification
    return redirect(url_for('login'))  # Redirige vers la page de login

# Route de traitement des fichiers uploadés
@app.route('/upload', methods=['POST'])
def upload_file():
    # Récupérer dynamiquement l'URL du frontend
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
    app.run(host='0.0.0.0', port=5000)  # Lance l'application sur toutes les interfaces réseau

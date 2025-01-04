import os
import uuid
import hashlib
import smtplib
from flask import request, jsonify
from . import app, db
from .models import FileUpload

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':  # Gérer la pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        file = request.files.get('file')

        if not file:
            return jsonify({'error': 'Fichier requis'}), 400

        file_id = str(uuid.uuid4())
        file_content = file.read()
        encrypted_data = hashlib.sha256(file_content).hexdigest()

        # Ajout de la logique pour sauvegarder le fichier
        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        upload_path = os.path.join(upload_dir, file.filename)
        
        # Sauvegarder le fichier
        with open(upload_path, 'wb') as f:
            f.write(file_content)

        new_file = FileUpload(
            id=file_id,
            filename=file.filename,
            encrypted_data=encrypted_data,
        )
        db.session.add(new_file)
        db.session.commit()

        # notify_user(file_id, email)  # Supprimer la notification

        response = jsonify({'file_id': file_id, 'message': 'Fichier reçu avec succès'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 201

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        response = jsonify({'error': str(e)})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Vérifie les identifiants fournis par le client et gère les requêtes CORS.
    """
    frontend_url = request.headers.get('Origin', 'http://localhost:3500')  # Dynamique

    if request.method == 'OPTIONS':  # Pré-requête CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    # Gestion de la méthode POST
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = "fake_jwt_token_for_demo_purposes"
        response = jsonify({"message": "Login réussi", "token": token})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 200
    else:
        response = jsonify({"error": "Identifiants invalides."})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 401

def notify_user(file_id, email):
    try:
        with smtplib.SMTP('localhost') as smtp:
            smtp.sendmail(
                from_addr='no-reply@itransfer.com',
                to_addrs=email,
                msg=f"Votre fichier a été uploadé avec succès. ID: {file_id}"
            )
        app.logger.info(f"Notification envoyée à {email} pour le fichier {file_id}")
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de la notification : {e}")
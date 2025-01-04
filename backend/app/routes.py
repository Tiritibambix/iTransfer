import os
import uuid
import hashlib
import smtplib
import json
from flask import request, jsonify, send_file
from . import app, db
from .models import FileUpload

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def send_email(to_email, file_id, filename):
    try:
        # Charger la configuration SMTP
        config_file_path = '/app/data/smtp_config.json'
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)

        # Créer le lien de téléchargement
        download_link = f"{BACKEND_URL}/download/{file_id}"

        # Configurer le message
        message = f"""
        Bonjour,

        Un fichier a été partagé avec vous via iTransfer.
        
        Fichier : {filename}
        Lien de téléchargement : {download_link}
        
        Ce lien expirera dans 7 jours.
        
        Cordialement,
        L'équipe iTransfer
        """

        # Configurer le serveur SMTP
        server = smtplib.SMTP(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        server.starttls()
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])

        # Envoyer l'email
        server.sendmail(
            smtp_config['smtp_sender_email'],
            to_email,
            f"From: {smtp_config['smtp_sender_email']}\r\n"
            f"To: {to_email}\r\n"
            f"Subject: iTransfer - Nouveau fichier partagé\r\n"
            f"\r\n{message}"
        )
        server.quit()
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {e}")
        return False

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
        recipient_email = request.form.get('email')  # Récupérer l'email du formulaire

        if not file:
            return jsonify({'error': 'Fichier requis'}), 400

        if not recipient_email:
            return jsonify({'error': 'Email du destinataire requis'}), 400

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

        # Créer l'entrée dans la base de données
        new_file = FileUpload(
            id=file_id,
            filename=file.filename,
            email=recipient_email,
            encrypted_data=encrypted_data
        )
        db.session.add(new_file)
        db.session.commit()

        # Envoyer l'email
        email_sent = send_email(recipient_email, file_id, file.filename)

        response_data = {
            'file_id': file_id,
            'message': 'Fichier reçu avec succès',
            'email_sent': email_sent
        }

        response = jsonify(response_data)
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

@app.route('/api/save-smtp-settings', methods=['POST', 'OPTIONS'])
def save_smtp_settings():
    if request.method == 'OPTIONS':  # Gérer la pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    data = request.json
    smtp_config = {
        "smtp_server": data.get("smtpServer"),
        "smtp_port": data.get("smtpPort"),
        "smtp_user": data.get("smtpUser"),
        "smtp_password": data.get("smtpPassword"),
        "smtp_sender_email": data.get("smtpSenderEmail"),
    }

    try:
        # Chemin vers le fichier de configuration dans le volume
        config_file_path = '/app/data/smtp_config.json'
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

        # Sauvegarder la configuration dans un fichier JSON
        with open(config_file_path, 'w') as config_file:
            json.dump(smtp_config, config_file)

        response = jsonify({"message": "Configuration SMTP enregistrée avec succès!"})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200
    except Exception as e:
        app.logger.error(f"Erreur lors de la sauvegarde des paramètres SMTP : {e}")
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
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

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        # Récupérer le fichier depuis la base de données
        file_upload = FileUpload.query.get_or_404(file_id)
        
        # Vérifier si le fichier existe dans le système de fichiers
        file_path = os.path.join('/app/uploads', file_upload.filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404

        # Envoyer le fichier
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_upload.filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement : {e}")
        return jsonify({'error': str(e)}), 500

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
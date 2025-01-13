import os
import uuid
import hashlib
import smtplib
import json
from flask import Blueprint, jsonify, request, current_app, send_file
from werkzeug.utils import secure_filename
from .extensions import db
from .models import FileUpload
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

bp = Blueprint('main', __name__)

def init_app(app):
    """Initialiser les configurations spécifiques aux routes"""
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME')
    app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD')
    app.config['BACKEND_URL'] = os.environ.get('BACKEND_URL', 'http://localhost:5000')

@bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'message': 'CORS preflight success'}), 200

        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé.")

        current_app.logger.info(f"Nom du fichier reçu : {file.filename}")

        # Générer un ID unique pour le fichier
        file_id = str(uuid.uuid4())
        
        # Sécuriser le nom du fichier
        filename = secure_filename(file.filename)
        
        # Sauvegarder le fichier
        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Sauvegarder les informations dans la base de données
        file_upload = FileUpload(id=file_id, filename=filename)
        db.session.add(file_upload)
        db.session.commit()
        
        # Envoyer l'email de notification
        email = request.form.get('email')
        if email:
            send_email(email, file_id, filename)

        return jsonify({
            "message": f"Fichier {filename} reçu avec succès",
            "file_id": file_id
        }), 201

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

@bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        current_app.logger.info(f"Tentative de téléchargement du fichier {file_id}")
        
        # Récupérer le fichier depuis la base de données
        file_upload = FileUpload.query.get_or_404(file_id)
        current_app.logger.info(f"Fichier trouvé dans la base de données : {file_upload.filename}")
        
        # Vérifier si le fichier existe dans le système de fichiers
        file_path = os.path.join('/app/uploads', file_upload.filename)
        current_app.logger.info(f"Chemin du fichier : {file_path}")
        
        if not os.path.exists(file_path):
            current_app.logger.error(f"Fichier non trouvé sur le disque : {file_path}")
            return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404

        current_app.logger.info(f"Fichier trouvé, envoi en cours...")
        
        try:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=file_upload.filename
            )
        except Exception as send_error:
            current_app.logger.error(f"Erreur lors de l'envoi du fichier : {str(send_error)}")
            return jsonify({'error': 'Erreur lors de l\'envoi du fichier'}), 500

    except Exception as e:
        current_app.logger.error(f"Erreur lors du téléchargement : {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback : {traceback.format_exc()}")
        return jsonify({'error': 'Erreur lors du téléchargement du fichier'}), 500

def send_email(to_email, file_id, filename):
    try:
        config_file_path = '/app/data/smtp_config.json'
        current_app.logger.info(f"Tentative de lecture de la configuration SMTP depuis {config_file_path}")
        
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)
            current_app.logger.info(f"Configuration SMTP chargée : {json.dumps({**smtp_config, 'smtp_password': '***'})}")

        # Créer le lien de téléchargement avec l'URL du backend configurée
        download_link = current_app.config['BACKEND_URL'] + f"/download/{file_id}"
        current_app.logger.info(f"Lien de téléchargement généré : {download_link}")

        # Configurer le message
        msg = MIMEMultipart()
        msg['From'] = smtp_config['smtp_sender_email']
        msg['To'] = to_email
        msg['Subject'] = f"Votre fichier {filename} est disponible"

        body = f"""
        Bonjour,

        Votre fichier {filename} a été uploadé avec succès.
        Vous pouvez le télécharger en cliquant sur ce lien :
        {download_link}

        Ce lien est valable pendant 24 heures.

        Cordialement,
        L'équipe iTransfer
        """
        msg.attach(MIMEText(body, 'plain'))

        # Se connecter au serveur SMTP
        current_app.logger.info(f"Tentative de connexion au serveur SMTP : {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        with smtplib.SMTP_SSL(smtp_config['smtp_server'].strip(), int(smtp_config['smtp_port'])) as server:
            server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
            server.send_message(msg)
            current_app.logger.info(f"Email envoyé avec succès à {to_email}")

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        raise

@bp.route('/api/test-smtp', methods=['POST', 'OPTIONS'])
def test_smtp():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight success'}), 200

    try:
        # Envoyer un email de test
        config_file_path = '/app/data/smtp_config.json'
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)

        # Créer un message de test
        msg = MIMEMultipart()
        msg['From'] = smtp_config['smtp_sender_email']
        msg['To'] = smtp_config['smtp_sender_email']  # Envoyer à soi-même
        msg['Subject'] = "Test de configuration SMTP"

        body = """
        Ceci est un email de test pour vérifier la configuration SMTP.
        Si vous recevez cet email, la configuration est correcte.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Se connecter au serveur SMTP
        with smtplib.SMTP_SSL(smtp_config['smtp_server'].strip(), int(smtp_config['smtp_port'])) as server:
            server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
            server.send_message(msg)

        return jsonify({'message': 'Test SMTP réussi!'}), 200

    except Exception as e:
        current_app.logger.error(f"Erreur lors du test SMTP : {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST', 'OPTIONS'])
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

    if username == current_app.config['ADMIN_USERNAME'] and password == current_app.config['ADMIN_PASSWORD']:
        token = "fake_jwt_token_for_demo_purposes"
        response = jsonify({"message": "Login réussi", "token": token})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 200
    else:
        response = jsonify({"error": "Identifiants invalides."})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        return response, 401

@bp.route('/api/save-smtp-settings', methods=['POST', 'OPTIONS'])
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
        current_app.logger.error(f"Erreur lors de la sauvegarde des paramètres SMTP : {e}")
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 500
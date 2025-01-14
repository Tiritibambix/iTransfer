import os
import uuid
import hashlib
import smtplib
import json
from flask import request, jsonify, send_file
from . import app, db
from .models import FileUpload

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
def get_backend_url():
    """
    Génère l'URL du backend en se basant sur la requête entrante
    """
    if not request:
        return os.environ.get('BACKEND_URL', 'http://localhost:5000')
    
    # Récupérer le protocole (http ou https)
    protocol = request.scheme
    
    # Récupérer l'hôte complet (hostname:port)
    host = request.headers.get('Host')
    if not host:
        # Fallback sur l'environnement ou la valeur par défaut
        return os.environ.get('BACKEND_URL', 'http://localhost:5000')
    
    return f"{protocol}://{host}"

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def send_notification_email(to_email, subject, message_content, smtp_config):
    server = None
    try:
        backend_url = get_backend_url()
        
        # Configurer le message
        email_message = f"""From: {smtp_config['smtp_sender_email']}
To: {to_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{message_content}"""

        # Utiliser SMTP_SSL pour le port 465
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())

        # Envoyer l'email
        app.logger.info(f"Envoi de l'email à {to_email}")
        server.sendmail(
            smtp_config['smtp_sender_email'],
            to_email,
            email_message.encode('utf-8')
        )
        app.logger.info("Email envoyé avec succès")
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        return False
    finally:
        if server:
            server.quit()

def send_recipient_notification(to_email, file_id, filename, smtp_config):
    backend_url = get_backend_url()
    download_link = f"{backend_url}/download/{file_id}"
    
    message = f"""
    Bonjour,

    Un fichier a été partagé avec vous via iTransfer.
    
    Fichier : {filename}
    Lien de téléchargement : {download_link}
    
    Ce lien expirera dans 7 jours.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    return send_notification_email(to_email, "iTransfer - Nouveau fichier partagé", message, smtp_config)

def send_sender_upload_confirmation(to_email, file_id, filename, smtp_config):
    backend_url = get_backend_url()
    download_link = f"{backend_url}/download/{file_id}"
    
    message = f"""
    Bonjour,

    Votre fichier a été uploadé avec succès sur iTransfer.
    
    Fichier : {filename}
    Lien de téléchargement : {download_link}
    
    Vous recevrez une notification lorsque le destinataire aura téléchargé le fichier.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    return send_notification_email(to_email, "iTransfer - Upload réussi", message, smtp_config)

def send_sender_download_notification(to_email, filename, smtp_config):
    message = f"""
    Bonjour,

    Le fichier que vous avez partagé via iTransfer a été téléchargé par le destinataire.
    
    Fichier : {filename}
    
    Cordialement,
    L'équipe iTransfer
    """
    
    return send_notification_email(to_email, "iTransfer - Fichier téléchargé", message, smtp_config)

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        file = request.files.get('file')
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')

        if not file or not email or not sender_email:
            return jsonify({'error': 'Fichier ou email manquant'}), 400

        file_id = str(uuid.uuid4())
        file_content = file.read()
        encrypted_data = hashlib.sha256(file_content).hexdigest()

        # Sauvegarder le fichier
        upload_dir = '/app/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        upload_path = os.path.join(upload_dir, file.filename)
        with open(upload_path, 'wb') as f:
            f.write(file_content)

        # Créer l'entrée dans la base de données
        new_file = FileUpload(
            id=file_id,
            filename=file.filename,
            email=email,
            sender_email=sender_email,
            encrypted_data=encrypted_data,
            downloaded=False
        )

        try:
            db.session.add(new_file)
            db.session.commit()
        except Exception as db_error:
            app.logger.error(f"Erreur base de données : {str(db_error)}")
            if os.path.exists(upload_path):
                os.remove(upload_path)
            raise db_error

        # Charger la configuration SMTP
        config_file_path = '/app/data/smtp_config.json'
        if not os.path.exists(config_file_path):
            return jsonify({'error': 'Configuration SMTP manquante'}), 500
            
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)
        
        # Envoyer les notifications
        recipient_notified = send_recipient_notification(email, file_id, file.filename, smtp_config)
        sender_notified = send_sender_upload_confirmation(sender_email, file_id, file.filename, smtp_config)
        
        if not recipient_notified or not sender_notified:
            return jsonify({'warning': 'Fichier uploadé mais problème avec les notifications'}), 200

        return jsonify({
            'success': True,
            'file_id': file_id,
            'message': 'Fichier uploadé avec succès'
        }), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {str(e)}")
        if 'upload_path' in locals() and os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-smtp-settings', methods=['POST', 'OPTIONS'])
def save_smtp_settings():
    if request.method == 'OPTIONS':
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
        response = jsonify({"error": "Une erreur interne est survenue."})
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
        file_upload = FileUpload.query.get_or_404(file_id)
        
        # Vérifier si le fichier existe dans le système de fichiers
        file_path = os.path.join('/app/uploads', file_upload.filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404

        # Si le fichier n'a pas encore été marqué comme téléchargé
        if not file_upload.downloaded:
            # Marquer le fichier comme téléchargé
            file_upload.downloaded = True
            db.session.commit()
            
            # Charger la configuration SMTP
            config_file_path = '/app/data/smtp_config.json'
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r') as config_file:
                    smtp_config = json.load(config_file)
                # Envoyer la notification à l'expéditeur
                send_sender_download_notification(file_upload.sender_email, file_upload.filename, smtp_config)
        
        # Envoyer le fichier
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_upload.filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement : {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-smtp', methods=['POST', 'OPTIONS'])
def test_smtp():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        # Charger la configuration SMTP
        config_file_path = '/app/data/smtp_config.json'
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)

        # Tenter d'envoyer un email de test
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        app.logger.info("Connexion SMTP établie pour le test")

        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'])
        app.logger.info("Connexion SMTP réussie pour le test")

        test_message = f"""From: {smtp_config['smtp_sender_email']}
To: {smtp_config['smtp_sender_email']}
Subject: Test de configuration SMTP iTransfer
Content-Type: text/plain; charset=utf-8

Ceci est un email de test pour vérifier la configuration SMTP d'iTransfer.
Si vous recevez cet email, la configuration est correcte."""

        server.sendmail(
            smtp_config['smtp_sender_email'],
            smtp_config['smtp_sender_email'],
            test_message.encode('utf-8')
        )
        
        server.quit()
        app.logger.info("Test SMTP réussi")

        response = jsonify({"success": True, "message": "Test SMTP réussi! Un email de test a été envoyé."})
        response.headers.add("Access-Control-Allow-Origin", '*')
        return response, 200

    except Exception as e:
        app.logger.error(f"Erreur lors du test SMTP : {str(e)}")
        response = jsonify({"success": False, "error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", '*')
        return response, 500
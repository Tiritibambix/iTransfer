import os
import uuid
import hashlib
import smtplib
import json
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from . import app, db
from .models import FileUpload

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
def get_backend_url():
    """
    Génère l'URL du backend en se basant sur la variable d'environnement BACKEND_URL
    ou sur la requête entrante en développement
    """
    # Utiliser BACKEND_URL s'il est défini
    backend_url = os.environ.get('BACKEND_URL')
    if backend_url:
        app.logger.info(f"Utilisation de l'URL backend depuis l'environnement : {backend_url}")
        return backend_url
    
    # Sinon, construire l'URL à partir de la requête (pour le développement)
    if not request:
        return 'http://localhost:5500'
    
    protocol = request.scheme
    host = request.headers.get('Host', 'localhost:5500')
    generated_url = f"{protocol}://{host}"
    app.logger.info(f"URL backend générée depuis la requête : {generated_url}")
    return generated_url

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def send_notification_email(to_email, subject, message_content, smtp_config):
    server = None
    try:
        backend_url = get_backend_url()
        app.logger.info(f"URL backend pour l'email : {backend_url}")
        
        # Configurer le message
        email_message = f"""From: {smtp_config['smtp_sender_email']}
To: {to_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{message_content}"""

        app.logger.info(f"Configuration du serveur SMTP : {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        # Utiliser SMTP_SSL pour le port 465
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        app.logger.info("Connexion SMTP établie")

        app.logger.info(f"Tentative de connexion avec l'utilisateur : {smtp_config['smtp_user']}")
        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
        app.logger.info("Connexion SMTP réussie")

        # Envoyer l'email
        app.logger.info(f"Envoi de l'email à {to_email}")
        app.logger.info(f"Contenu de l'email :\n{email_message}")
        server.sendmail(
            smtp_config['smtp_sender_email'],
            to_email,
            email_message.encode('utf-8')
        )
        app.logger.info("Email envoyé avec succès")
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        app.logger.error(f"Type d'erreur : {type(e).__name__}")
        if hasattr(e, 'smtp_error'):
            app.logger.error(f"Erreur SMTP : {e.smtp_error}")
        if hasattr(e, 'smtp_code'):
            app.logger.error(f"Code SMTP : {e.smtp_code}")
        return False
    finally:
        if server:
            try:
                server.quit()
                app.logger.info("Connexion SMTP fermée")
            except Exception as e:
                app.logger.error(f"Erreur lors de la fermeture de la connexion SMTP : {str(e)}")

def send_recipient_notification(to_email, file_id, filename, smtp_config):
    app.logger.info(f"Préparation de la notification pour le destinataire : {to_email}")
    backend_url = get_backend_url()
    download_link = f"{backend_url}/download/{file_id}"
    app.logger.info(f"Lien de téléchargement généré : {download_link}")
    
    message = f"""
    Bonjour,

    Un fichier a été partagé avec vous via iTransfer.
    
    Fichier : {filename}
    Lien de téléchargement : {download_link}
    
    Ce lien expirera dans 7 jours.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la notification au destinataire")
    success = send_notification_email(to_email, "iTransfer - Nouveau fichier partagé", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la notification au destinataire : {to_email}")
    return success

def send_sender_upload_confirmation(to_email, file_id, filename, smtp_config):
    app.logger.info(f"Préparation de la confirmation pour l'expéditeur : {to_email}")
    backend_url = get_backend_url()
    
    message = f"""
    Bonjour,

    Votre fichier a été uploadé avec succès sur iTransfer.
    
    Fichier : {filename}
    ID : {file_id}
    
    Le destinataire recevra un email avec le lien de téléchargement.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la confirmation à l'expéditeur")
    success = send_notification_email(to_email, "iTransfer - Upload réussi", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la confirmation à l'expéditeur : {to_email}")
    return success

def send_sender_download_notification(to_email, filename, smtp_config):
    app.logger.info(f"Préparation de la notification pour l'expéditeur : {to_email}")
    message = f"""
    Bonjour,

    Le fichier que vous avez partagé via iTransfer a été téléchargé par le destinataire.
    
    Fichier : {filename}
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la notification à l'expéditeur")
    success = send_notification_email(to_email, "iTransfer - Fichier téléchargé", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la notification à l'expéditeur : {to_email}")
    return success

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight success'}), 200

    try:
        # Vérification des données requises
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        file = request.files['file']
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')

        if not file or not email or not sender_email:
            return jsonify({'error': 'Fichier ou email manquant'}), 400
        
        if not file.filename:
            return jsonify({'error': 'Nom de fichier invalide'}), 400

        # Génération d'un ID unique et sécurisation du nom de fichier
        file_id = str(uuid.uuid4())
        file_content = file.read()
        encrypted_data = hashlib.sha256(file_content).hexdigest()
        safe_filename = secure_filename(file.filename)
        
        # Création du chemin de fichier unique
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{safe_filename}")
        
        try:
            # Sauvegarde du fichier
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(file_content)
        except Exception as e:
            app.logger.error(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
            return jsonify({'error': 'Erreur lors de la sauvegarde du fichier'}), 500

        try:
            # Création de l'entrée dans la base de données
            new_file = FileUpload(
                id=file_id,
                filename=safe_filename,
                email=email,
                sender_email=sender_email,
                encrypted_data=encrypted_data,
                downloaded=False
            )
            db.session.add(new_file)
            db.session.commit()
        except Exception as db_error:
            app.logger.error(f"Erreur base de données: {str(db_error)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': 'Erreur lors de l\'enregistrement en base de données'}), 500

        # Chargement de la configuration SMTP
        try:
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)
        except Exception as e:
            app.logger.error(f"Erreur lors du chargement de la configuration SMTP: {str(e)}")
            return jsonify({'warning': 'Fichier uploadé mais impossible d\'envoyer les notifications'}), 200

        # Envoi des notifications
        notification_errors = []
        if not send_recipient_notification(email, file_id, safe_filename, smtp_config):
            notification_errors.append("destinataire")
        if not send_sender_upload_confirmation(sender_email, file_id, safe_filename, smtp_config):
            notification_errors.append("expéditeur")

        response_data = {
            'success': True,
            'file_id': file_id,
            'message': 'Fichier uploadé avec succès'
        }

        if notification_errors:
            response_data['warning'] = f"Impossible d'envoyer les notifications aux destinataires suivants: {', '.join(notification_errors)}"

        return jsonify(response_data), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

@app.route('/api/save-smtp-settings', methods=['POST', 'OPTIONS'])
def save_smtp_settings():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

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
        config_file_path = app.config['SMTP_CONFIG_PATH']
        
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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_upload.id}_{file_upload.filename}")
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404

        # Si le fichier n'a pas encore été marqué comme téléchargé
        if not file_upload.downloaded:
            # Marquer le fichier comme téléchargé
            file_upload.downloaded = True
            db.session.commit()
            
            # Charger la configuration SMTP
            try:
                with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                    smtp_config = json.load(config_file)
                # Envoyer la notification à l'expéditeur
                send_sender_download_notification(file_upload.sender_email, file_upload.filename, smtp_config)
            except Exception as e:
                app.logger.error(f"Erreur lors du chargement de la configuration SMTP: {str(e)}")

        # Envoyer le fichier
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_upload.filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement : {str(e)}")
        return jsonify({'error': 'An internal error has occurred!'}), 500

@app.route('/api/test-smtp', methods=['POST', 'OPTIONS'])
def test_smtp():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", '*')
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        app.logger.info("Début du test SMTP")
        # Charger la configuration SMTP
        try:
            app.logger.info(f"Tentative de lecture de la configuration SMTP depuis {app.config['SMTP_CONFIG_PATH']}")
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)
                app.logger.info(f"Configuration SMTP chargée : serveur={smtp_config['smtp_server']}, port={smtp_config['smtp_port']}, user={smtp_config['smtp_user']}, sender={smtp_config['smtp_sender_email']}")
        except Exception as e:
            app.logger.error(f"Erreur lors du chargement de la configuration SMTP: {str(e)}")
            return jsonify({'error': 'Configuration SMTP manquante'}), 500

        # Tenter d'envoyer un email de test
        app.logger.info(f"Tentative de connexion à {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        app.logger.info("Connexion SMTP établie pour le test")

        app.logger.info(f"Tentative de connexion avec l'utilisateur {smtp_config['smtp_user']}")
        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'])
        app.logger.info("Connexion SMTP réussie pour le test")

        test_message = f"""From: {smtp_config['smtp_sender_email']}
To: {smtp_config['smtp_sender_email']}
Subject: Test de configuration SMTP iTransfer
Content-Type: text/plain; charset=utf-8

Ceci est un email de test pour vérifier la configuration SMTP d'iTransfer.
Si vous recevez cet email, la configuration est correcte."""

        app.logger.info(f"Tentative d'envoi de l'email de test à {smtp_config['smtp_sender_email']}")
        server.sendmail(
            smtp_config['smtp_sender_email'],
            smtp_config['smtp_sender_email'],
            test_message.encode('utf-8')
        )
        
        server.quit()
        app.logger.info("Test SMTP réussi, email envoyé avec succès")

        response = jsonify({"success": True, "message": "Test SMTP réussi! Un email de test a été envoyé."})
        response.headers.add("Access-Control-Allow-Origin", '*')
        return response, 200

    except Exception as e:
        app.logger.error(f"Erreur lors du test SMTP : {str(e)}")
        app.logger.error(f"Type d'erreur : {type(e).__name__}")
        app.logger.error(f"Détails de l'erreur : {str(e)}")
        if hasattr(e, 'smtp_error'):
            app.logger.error(f"Erreur SMTP : {e.smtp_error}")
        if hasattr(e, 'smtp_code'):
            app.logger.error(f"Code SMTP : {e.smtp_code}")
        response = jsonify({"success": False, "error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", '*')
        return response, 500
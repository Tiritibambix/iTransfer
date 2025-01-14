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

def send_email(to_email, file_id, filename, sender_email=None):
    server = None
    try:
        # Charger la configuration SMTP
        config_file_path = '/app/data/smtp_config.json'
        app.logger.info(f"Tentative de lecture de la configuration SMTP depuis {config_file_path}")
        
        if not os.path.exists(config_file_path):
            app.logger.error(f"Fichier de configuration SMTP introuvable : {config_file_path}")
            return False
        
        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)
            app.logger.info(f"Configuration SMTP chargée : {json.dumps({**smtp_config, 'smtp_password': '***'})}")

        # Vérifier les champs requis
        required_fields = ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_sender_email']
        for field in required_fields:
            if field not in smtp_config or not smtp_config[field]:
                app.logger.error(f"Champ SMTP manquant ou vide : {field}")
                return False

        # Créer le lien de téléchargement avec l'URL dynamique
        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"

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

        # Message pour l'expéditeur après l'upload
        if sender_email:
            message_sender = f"""
            Bonjour,

            Votre fichier '{filename}' a été uploadé avec succès.
            
            Lien de téléchargement pour le destinataire : {download_link}
            
            Cordialement,
            L'équipe iTransfer
            """
            email_message_sender = f"""From: {smtp_config['smtp_sender_email']}
To: {sender_email}
Subject: Confirmation d'upload réussi
Content-Type: text/plain; charset=utf-8

{message_sender}"""

            # Envoyer l'email à l'expéditeur
            app.logger.info(f"Envoi de l'email de confirmation à l'expéditeur {sender_email}")
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
            server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
            server.sendmail(smtp_config['smtp_sender_email'], sender_email, email_message_sender.encode('utf-8'))

        app.logger.info(f"Tentative de connexion au serveur SMTP : {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        
        # Utiliser SMTP_SSL pour le port 465
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        app.logger.info("Connexion SMTP établie")

        # Se connecter
        app.logger.info(f"Tentative de connexion avec l'utilisateur : {smtp_config['smtp_user']}")
        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
        app.logger.info("Connexion SMTP réussie")

        # Préparer l'email
        email_message = f"""From: {smtp_config['smtp_sender_email']}
To: {to_email}
Subject: iTransfer - Nouveau fichier partagé
Content-Type: text/plain; charset=utf-8

{message}"""

        # Envoyer l'email
        app.logger.info(f"Envoi de l'email à {to_email}")
        server.sendmail(
            smtp_config['smtp_sender_email'],
            to_email,
            email_message.encode('utf-8')
        )
        app.logger.info("Email envoyé avec succès")
        
        if server:
            server.quit()
        return True

    except FileNotFoundError as e:
        app.logger.error(f"Erreur de fichier SMTP : {str(e)}")
        return False
    except json.JSONDecodeError as e:
        app.logger.error(f"Erreur de format JSON dans la configuration SMTP : {str(e)}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        app.logger.error(f"Erreur d'authentification SMTP : {str(e)}")
        return False
    except smtplib.SMTPException as e:
        app.logger.error(f"Erreur SMTP : {str(e)}")
        return False
    except Exception as e:
        app.logger.error(f"Erreur inattendue lors de l'envoi de l'email : {str(e)}")
        import traceback
        app.logger.error(f"Traceback : {traceback.format_exc()}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

def send_confirmation_email(to_email, filename):
    try:
        # Charger la configuration SMTP
        config_file_path = '/app/data/smtp_config.json'
        if not os.path.exists(config_file_path):
            app.logger.error(f"Fichier de configuration SMTP introuvable : {config_file_path}")
            return False

        with open(config_file_path, 'r') as config_file:
            smtp_config = json.load(config_file)

        # Configurer le message de confirmation
        message = f"""
        Bonjour,

        Votre fichier '{filename}' a été téléchargé avec succès par le destinataire.

        Cordialement,
        L'équipe iTransfer
        """

        # Préparer l'email
        email_message = f"""From: {smtp_config['smtp_sender_email']}
To: {to_email}
Subject: Confirmation de téléchargement de fichier
Content-Type: text/plain; charset=utf-8

{message}"""

        # Envoyer l'email
        server = smtplib.SMTP_SSL(smtp_config['smtp_server'], int(smtp_config['smtp_port']))
        server.login(smtp_config['smtp_user'].strip(), smtp_config['smtp_password'].strip())
        server.sendmail(smtp_config['smtp_sender_email'], to_email, email_message.encode('utf-8'))
        server.quit()
        return True

    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email de confirmation : {str(e)}")
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
        sender_email = request.form.get('senderEmail')  # Récupérer l'email de l'expéditeur

        if not file:
            return jsonify({'error': 'Fichier requis'}), 400

        if not recipient_email:
            return jsonify({'error': 'Email du destinataire requis'}), 400

        if not sender_email:
            return jsonify({'error': 'Email de l\'expéditeur requis'}), 400

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

        try:
            db.session.add(new_file)
            db.session.commit()
        except Exception as db_error:
            app.logger.error(f"Erreur base de données : {str(db_error)}")
            # Supprimer le fichier en cas d'erreur
            if os.path.exists(upload_path):
                os.remove(upload_path)
            raise db_error

        # Envoyer l'email
        try:
            email_sent = send_email(recipient_email, file_id, file.filename, sender_email)
            if not email_sent:
                app.logger.error("L'envoi de l'email a échoué")
            else:
                # Envoyer un email de confirmation à l'expéditeur
                send_confirmation_email(sender_email, file.filename)
        except Exception as email_error:
            app.logger.error(f"Erreur lors de l'envoi de l'email : {str(email_error)}")
            email_sent = False

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
        app.logger.error(f"Erreur lors de l'upload : {str(e)}")
        # Si une erreur survient, on s'assure de nettoyer le fichier s'il existe
        if 'upload_path' in locals() and os.path.exists(upload_path):
            os.remove(upload_path)
        response = jsonify({'error': 'Erreur lors de l\'upload. Veuillez vérifier que l\'email est valide et réessayer.'})
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
    """
    Télécharger un fichier en utilisant son ID
    """
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
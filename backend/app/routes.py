import os
import uuid
import hashlib
import smtplib
import json
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid, formataddr
from . import app, db
from .models import FileUpload
from email.utils import formatdate
import jwt
from datetime import datetime, timedelta
import zipfile
import shutil

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
def get_backend_url():
    """
    Génère l'URL du backend en se basant sur la variable d'environnement BACKEND_URL
    ou sur la requête entrante en développement
    """
    # Utiliser BACKEND_URL s'il est défini (environnement de production)
    backend_url = os.environ.get('BACKEND_URL')
    if backend_url:
        # Forcer HTTPS si configuré
        if app.config['FORCE_HTTPS']:
            if backend_url.startswith('http://'):
                backend_url = 'https://' + backend_url[7:]
            elif not backend_url.startswith('https://'):
                backend_url = 'https://' + backend_url
            
        app.logger.info(f"Utilisation de l'URL backend depuis l'environnement : {backend_url}")
        return backend_url
    
    # Sinon, construire l'URL à partir de la requête (pour le développement)
    if not request:
        protocol = 'https' if app.config['FORCE_HTTPS'] else 'http'
        return f'{protocol}://localhost:5500'
    
    # En développement, on utilise le protocole configuré
    protocol = 'https' if app.config['FORCE_HTTPS'] else request.scheme
    host = request.headers.get('Host', 'localhost:5500')
    
    # Si on est derrière un proxy, on vérifie le X-Forwarded-Proto
    if app.config['PROXY_COUNT'] > 0 and request.headers.get('X-Forwarded-Proto'):
        protocol = request.headers.get('X-Forwarded-Proto')
    
    generated_url = f"{protocol}://{host}"
    app.logger.info(f"URL backend générée depuis la requête : {generated_url}")
    return generated_url

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

def send_notification_email(to_email, subject, message_content, smtp_config):
    server = None
    try:
        backend_url = get_backend_url()
        app.logger.info(f"URL backend pour l'email : {backend_url}")
        
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.utils import formatdate, make_msgid, formataddr
        
        # Créer un message MIME multipart
        msg = MIMEMultipart('alternative')
        
        # Utiliser un nom d'affichage professionnel
        sender_name = "iTransfer"
        sender_email = smtp_config['smtp_sender_email']
        
        # Ajouter les en-têtes standards avec un format plus professionnel
        msg['From'] = formataddr((sender_name, sender_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[1])
        
        # En-têtes supplémentaires pour améliorer la délivrabilité
        msg['Return-Path'] = sender_email
        msg['X-Mailer'] = 'iTransfer Secure File Transfer System'
        msg['X-Priority'] = '3'
        msg['List-Unsubscribe'] = f'<mailto:{sender_email}?subject=unsubscribe>'
        msg['Precedence'] = 'bulk'
        msg['Auto-Submitted'] = 'auto-generated'
        
        # Ajouter le contenu en texte brut
        text_part = MIMEText(message_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Préparer le contenu du message pour HTML
        formatted_content = (
            message_content.replace("Bonjour,", "<p>Bonjour,</p>")
            .replace("Cordialement,", "<p>Cordialement,</p>")
            .replace("L'équipe iTransfer", "<strong>L'équipe iTransfer</strong>")
            .replace('\n\n', '</p><p>')
            .replace('\n', '<br>')
        )
        
        # Créer une version HTML plus professionnelle
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">{title}</h2>
                {content}
            </div>
            <div style="font-size: 12px; color: #666; text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                <p>Cet email a été envoyé automatiquement par iTransfer. Merci de ne pas y répondre.</p>
            </div>
        </body>
        </html>
        '''
        
        html_content = html_template.format(
            title=subject,
            content=formatted_content
        )
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        app.logger.info(f"Configuration du serveur SMTP : {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        
        # Choisir le type de connexion en fonction du port
        port = int(smtp_config['smtp_port'])
        if port == 465:
            # Port 465 : SMTP_SSL
            app.logger.info("Utilisation de SMTP_SSL (port 465)")
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port)
        else:
            # Port 587 ou autre : SMTP + STARTTLS
            app.logger.info(f"Utilisation de SMTP + STARTTLS (port {port})")
            server = smtplib.SMTP(smtp_config['smtp_server'], port)
            server.starttls()
        
        app.logger.info("Connexion SMTP établie")
        
        app.logger.info(f"Tentative de connexion avec l'utilisateur : {smtp_config['smtp_user']}")
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
        app.logger.info("Connexion SMTP réussie")
        
        app.logger.info(f"Envoi de l'email à {to_email}")
        app.logger.info(f"Contenu de l'email :\n{msg.as_string()}")
        
        server.send_message(msg)
        app.logger.info("Email envoyé avec succès")
        return True
        
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        return False
        
    finally:
        if server:
            try:
                server.quit()
                app.logger.info("Connexion SMTP fermée")
            except Exception as e:
                app.logger.error(f"Erreur lors de la fermeture de la connexion SMTP : {str(e)}")

def send_recipient_notification(to_email, file_id, filename, smtp_config):
    """Envoie une notification au destinataire avec le lien de téléchargement"""
    app.logger.info(f"Préparation de la notification pour le destinataire : {to_email}")
    backend_url = get_backend_url()
    app.logger.info(f"URL backend : {backend_url}")
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
    """Envoie une confirmation à l'expéditeur après l'upload"""
    app.logger.info(f"Préparation de la confirmation pour l'expéditeur : {to_email}")
    backend_url = get_backend_url()
    app.logger.info(f"URL backend : {backend_url}")
    download_link = f"{backend_url}/download/{file_id}"
    app.logger.info(f"Lien de téléchargement généré : {download_link}")
    
    message = f"""
    Bonjour,

    Votre fichier a été uploadé avec succès sur iTransfer.
    
    Fichier : {filename}
    ID : {file_id}
    Lien de téléchargement : {download_link}
    
    Une notification a été envoyée au destinataire avec ce même lien.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la confirmation à l'expéditeur")
    success = send_notification_email(to_email, "iTransfer - Upload réussi", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la confirmation à l'expéditeur : {to_email}")
    return success

def send_sender_download_notification(to_email, filename, smtp_config):
    """Envoie une notification à l'expéditeur quand le fichier est téléchargé"""
    app.logger.info(f"Préparation de la notification pour l'expéditeur : {to_email}")
    
    message = f"""
    Bonjour,

    Le fichier que vous avez partagé via iTransfer a été téléchargé par le destinataire.
    
    Fichier : {filename}
    Date de téléchargement : {formatdate(localtime=True)}
    
    Cette notification vous est envoyée à titre informatif.
    
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
        app.logger.info("Début du traitement de l'upload")
        if 'files[]' not in request.files:
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')
        if email:
            email = email.lower().strip()
        if sender_email:
            sender_email = sender_email.lower().strip()

        app.logger.info(f"Nombre de fichiers reçus : {len(files)}")
        app.logger.info(f"Email destinataire : {email}")
        app.logger.info(f"Email expéditeur : {sender_email}")

        if not files or not email or not sender_email:
            return jsonify({'error': 'Fichiers ou email manquant'}), 400

        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        
        file_list = []
        total_size = 0
        
        try:
            for file, path in zip(files, paths):
                if file.filename:
                    relative_path = path.lstrip('/')
                    full_path = os.path.join(temp_dir, relative_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    file.save(full_path)
                    file_size = os.path.getsize(full_path)
                    total_size += file_size
                    file_list.append({
                        'name': relative_path,
                        'size': file_size
                    })
            
            zip_filename = f"transfer_{file_id}.zip"
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            with open(zip_path, 'rb') as f:
                encrypted_data = hashlib.sha256(f.read()).hexdigest()
            
            new_file = FileUpload(
                id=file_id,
                filename=zip_filename,
                email=email,
                sender_email=sender_email,
                encrypted_data=encrypted_data,
                downloaded=False
            )
            db.session.add(new_file)
            db.session.commit()
            app.logger.info("Entrée créée dans la base de données")
            
        except Exception as e:
            app.logger.error(f"Erreur lors du traitement des fichiers: {str(e)}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return jsonify({'error': 'Erreur lors du traitement des fichiers'}), 500
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)
        
        files_summary = "\n".join([f"- {f['name']} ({format_size(f['size'])})" for f in file_list])
        total_size_formatted = format_size(total_size)

        notification_errors = []
        
        app.logger.info("Tentative d'envoi de la notification au destinataire")
        if not send_recipient_notification_with_files(email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
            app.logger.error("Échec de l'envoi au destinataire")
            notification_errors.append("destinataire")
        
        app.logger.info("Tentative d'envoi de la confirmation à l'expéditeur")
        if not send_sender_upload_confirmation_with_files(sender_email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
            app.logger.error("Échec de l'envoi à l'expéditeur")
            notification_errors.append("expéditeur")

        response_data = {
            'success': True,
            'file_id': file_id,
            'message': 'Fichiers uploadés avec succès'
        }

        if notification_errors:
            response_data['warning'] = f"Impossible d'envoyer les notifications aux destinataires suivants: {', '.join(notification_errors)}"

        app.logger.info("Upload terminé avec succès")
        return jsonify(response_data), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload: {str(e)}")
        if 'zip_path' in locals() and os.path.exists(zip_path):
            os.remove(zip_path)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

def format_size(size):
    """Formate la taille en bytes en une chaîne lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def send_recipient_notification_with_files(to_email, file_id, zip_filename, files_summary, total_size, smtp_config):
    """Envoie une notification au destinataire avec la liste des fichiers"""
    app.logger.info(f"Préparation de la notification pour le destinataire : {to_email}")
    backend_url = get_backend_url()
    app.logger.info(f"URL backend : {backend_url}")
    download_link = f"{backend_url}/download/{file_id}"
    app.logger.info(f"Lien de téléchargement généré : {download_link}")
    
    message = f"""
    Bonjour,

    Des fichiers ont été partagés avec vous via iTransfer.
    
    Archive ZIP : {zip_filename}
    Taille totale : {total_size}
    
    Contenu de l'archive :
    {files_summary}
    
    Lien de téléchargement : {download_link}
    
    Ce lien expirera dans 7 jours.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la notification au destinataire")
    success = send_notification_email(to_email, "iTransfer - Nouveaux fichiers partagés", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la notification au destinataire : {to_email}")
    return success

def send_sender_upload_confirmation_with_files(to_email, file_id, zip_filename, files_summary, total_size, smtp_config):
    """Envoie une confirmation à l'expéditeur avec la liste des fichiers"""
    app.logger.info(f"Préparation de la confirmation pour l'expéditeur : {to_email}")
    backend_url = get_backend_url()
    app.logger.info(f"URL backend : {backend_url}")
    download_link = f"{backend_url}/download/{file_id}"
    app.logger.info(f"Lien de téléchargement généré : {download_link}")
    
    message = f"""
    Bonjour,

    Vos fichiers ont été uploadés avec succès sur iTransfer.
    
    Archive ZIP : {zip_filename}
    Taille totale : {total_size}
    
    Contenu de l'archive :
    {files_summary}
    
    ID : {file_id}
    Lien de téléchargement : {download_link}
    
    Une notification a été envoyée au destinataire avec ce même lien.
    
    Cordialement,
    L'équipe iTransfer
    """
    
    app.logger.info("Envoi de la confirmation à l'expéditeur")
    success = send_notification_email(to_email, "iTransfer - Upload réussi", message, smtp_config)
    if not success:
        app.logger.error(f"Échec de l'envoi de la confirmation à l'expéditeur : {to_email}")
    return success

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
        config_file_path = app.config['SMTP_CONFIG_PATH']
        
        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

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

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = jwt.encode(
            {
                'user': username,
                'exp': datetime.utcnow() + timedelta(days=1)
            },
            JWT_SECRET_KEY,
            algorithm='HS256'
        )
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
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_upload.id}_{file_upload.filename}")
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404

        if not file_upload.downloaded:
            file_upload.downloaded = True
            db.session.commit()
            
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)
            send_sender_download_notification(file_upload.sender_email, file_upload.filename, smtp_config)

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
        
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)
        
        app.logger.info(f"Tentative de connexion à {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        
        port = int(smtp_config['smtp_port'])
        if port == 465:
            app.logger.info("Utilisation de SMTP_SSL (port 465)")
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port)
        else:
            app.logger.info(f"Utilisation de SMTP + STARTTLS (port {port})")
            server = smtplib.SMTP(smtp_config['smtp_server'], port)
            server.starttls()
            
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
        response = jsonify({"success": False, "error": "An internal error has occurred. Please try again later."})
        response.headers.add("Access-Control-Allow-Origin", '*')
        return response, 500
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
import traceback

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

def send_email(to_email, subject, message_content, html_content):
    try:
        backend_url = get_backend_url()
        app.logger.info(f"=== ENVOI D'EMAIL ===")
        app.logger.info(f"À: {to_email}")
        app.logger.info(f"Sujet: {subject}")
        app.logger.info(f"URL backend: {backend_url}")
        
        # Créer un message MIME multipart
        msg = MIMEMultipart('alternative')
        
        # Utiliser un nom d'affichage professionnel
        sender_name = "iTransfer"
        sender_email = "no-reply@itransfer.com"
        app.logger.info(f"De: {sender_name} <{sender_email}>")
        
        # Ajouter les en-têtes standards avec un format plus professionnel
        msg['From'] = formataddr((sender_name, sender_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[1])
        
        # En-têtes anti-spam supplémentaires
        msg.add_header('List-Unsubscribe', f'<mailto:{sender_email}?subject=unsubscribe>')
        msg.add_header('Precedence', 'bulk')
        msg.add_header('Auto-Submitted', 'auto-generated')
        msg.add_header('X-Auto-Response-Suppress', 'OOF, DR, RN, NRN, AutoReply')
        msg.add_header('Feedback-ID', 'iTransfer:FileTransfer')
        msg.add_header('X-Report-Abuse', f'Please report abuse to {sender_email}')
        
        app.logger.info("En-têtes d'email configurés")
        
        # Ajouter le contenu en texte brut
        text_part = MIMEText(message_content, 'plain', 'utf-8')
        msg.attach(text_part)
        app.logger.info("Contenu texte attaché")
        
        # Ajouter le contenu HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        app.logger.info("Contenu HTML attaché")
        
        # Configuration et envoi de l'email
        app.logger.info("=== CONFIGURATION SMTP ===")
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)
            app.logger.info(f"Configuration SMTP chargée: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        
        port = int(smtp_config['smtp_port'])
        app.logger.info(f"Connexion au serveur SMTP: {smtp_config['smtp_server']}:{port}")
        
        if port == 465:
            app.logger.info("Utilisation de SMTP_SSL")
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port)
        else:
            app.logger.info("Utilisation de SMTP avec STARTTLS")
            server = smtplib.SMTP(smtp_config['smtp_server'], port)
            server.starttls()
        
        app.logger.info("Tentative de connexion SMTP...")
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
        app.logger.info("Connexion SMTP réussie")
        
        app.logger.info("Envoi de l'email...")
        server.send_message(msg)
        app.logger.info("Email envoyé avec succès")
        return True
        
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return False
        
    finally:
        if 'server' in locals():
            try:
                server.quit()
                app.logger.info("Connexion SMTP fermée")
            except Exception as e:
                app.logger.error(f"Erreur lors de la fermeture de la connexion SMTP : {str(e)}")

# Template HTML partagé pour les emails
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { margin-bottom: 20px; }
        .info { margin-bottom: 20px; }
        .files { 
            background-color: #f5f5f5; 
            padding: 15px; 
            border-radius: 4px; 
            margin-bottom: 20px;
        }
        .download-link { 
            display: inline-block; 
            background-color: #007bff; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 20px 0;
        }
        .download-link:hover { background-color: #0056b3; }
        .expiry { 
            font-size: 0.9em; 
            color: #666; 
            font-style: italic; 
        }
        .footer { 
            margin-top: 30px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            font-size: 0.9em; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <p>Bonjour,</p>
            <p>Des fichiers ont été partagés avec vous via iTransfer.</p>
        </div>
        
        <div class="info">
            <p><strong>Archive ZIP :</strong> {zip_name}</p>
            <p><strong>Taille totale :</strong> {total_size}</p>
        </div>
        
        <div class="files">
            <strong>Contenu de l'archive :</strong><br>
            {files}
        </div>
        
        <a href="{download_url}" class="download-link">Télécharger les fichiers</a>
        
        <p class="expiry">Ce lien expirera dans 7 jours.</p>
        
        <div class="footer">
            <p>Cordialement,<br>L'équipe iTransfer</p>
        </div>
    </div>
</body>
</html>
'''

def send_recipient_notification_with_files(to_email, file_id, zip_name, files_summary, total_size, smtp_config):
    """Envoie une notification au destinataire avec la liste des fichiers"""
    app.logger.info(f"Préparation de la notification pour le destinataire : {to_email}")
    backend_url = get_backend_url()
    download_url = f"{backend_url}/download/{file_id}"
    success = True

    # Créer le contenu du message
    message_content = f"""
    Bonjour,

    Des fichiers ont été partagés avec vous via iTransfer.

    Archive ZIP : {zip_name}
    Taille totale : {total_size}

    Contenu de l'archive :
    {files_summary}

    Lien de téléchargement : {download_url}

    Ce lien expirera dans 7 jours.

    Cordialement,
    L'équipe iTransfer
    """

    # Formater la liste des fichiers pour HTML
    files_html = []
    current_folder = None
    
    for line in files_summary.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Dossier '):
            current_folder = line.replace('Dossier ', '')
            files_html.append(f'<div style="margin-top: 10px;"><strong>{current_folder}</strong></div>')
        else:
            file_info = line.strip('- ')
            if current_folder:
                files_html.append(f'<div style="margin-left: 20px;">└─ {file_info}</div>')
            else:
                files_html.append(f'<div>• {file_info}</div>')

    # Créer le contenu HTML
    html_content = html_template.format(
        zip_name=zip_name,
        total_size=total_size,
        files='\n'.join(files_html),
        download_url=download_url
    )

    try:
        send_email(to_email, "Transfert de fichiers via iTransfer", message_content, html_content)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        success = False

    return success

def send_sender_upload_confirmation_with_files(to_email, file_id, zip_name, files_summary, total_size, smtp_config):
    """Envoie une confirmation à l'expéditeur avec la liste des fichiers"""
    app.logger.info(f"Préparation de la confirmation pour l'expéditeur : {to_email}")
    backend_url = get_backend_url()
    download_url = f"{backend_url}/download/{file_id}"
    success = True

    # Créer le contenu du message
    message_content = f"""
    Bonjour,

    Vos fichiers ont été uploadés avec succès sur iTransfer.

    Archive ZIP : {zip_name}
    Taille totale : {total_size}

    Contenu de l'archive :
    {files_summary}

    ID : {file_id}
    Lien de téléchargement : {download_url}

    Une notification a été envoyée au destinataire avec ce même lien.

    Cordialement,
    L'équipe iTransfer
    """

    # Formater la liste des fichiers pour HTML
    files_html = []
    current_folder = None
    
    for line in files_summary.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Dossier '):
            current_folder = line.replace('Dossier ', '')
            files_html.append(f'<div style="margin-top: 10px;"><strong>{current_folder}</strong></div>')
        else:
            file_info = line.strip('- ')
            if current_folder:
                files_html.append(f'<div style="margin-left: 20px;">└─ {file_info}</div>')
            else:
                files_html.append(f'<div>• {file_info}</div>')

    # Créer le contenu HTML final
    html_content = html_template.format(
        zip_name=zip_name,
        total_size=total_size,
        files='\n'.join(files_html),
        download_url=download_url
    )

    try:
        send_email(to_email, "Confirmation d'envoi de fichiers via iTransfer", message_content, html_content)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de la confirmation : {str(e)}")
        success = False

    return success

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight success'}), 200

    try:
        app.logger.info("=== DÉBUT DE L'UPLOAD ===")
        app.logger.info(f"Headers reçus: {dict(request.headers)}")
        
        if 'files[]' not in request.files:
            app.logger.error("Aucun fichier dans la requête")
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')
        
        app.logger.info(f"Email destinataire (brut): {email}")
        app.logger.info(f"Email expéditeur (brut): {sender_email}")
        
        if email:
            email = email.lower().strip()
        if sender_email:
            sender_email = sender_email.lower().strip()

        app.logger.info(f"Email destinataire (nettoyé): {email}")
        app.logger.info(f"Email expéditeur (nettoyé): {sender_email}")
        app.logger.info(f"Nombre de fichiers reçus: {len(files)}")
        app.logger.info(f"Chemins reçus: {paths}")

        if not files or not email or not sender_email:
            app.logger.error(f"Validation échouée - Files: {bool(files)}, Email: {bool(email)}, Sender: {bool(sender_email)}")
            return jsonify({'error': 'Fichiers ou email manquant'}), 400

        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        app.logger.info(f"ID généré: {file_id}")
        app.logger.info(f"Dossier temporaire: {temp_dir}")
        
        file_list = []
        total_size = 0
        
        try:
            app.logger.info("=== TRAITEMENT DES FICHIERS ===")
            folders = {}
            for file, path in zip(files, paths):
                if file.filename:
                    app.logger.info(f"Traitement du fichier: {file.filename}")
                    app.logger.info(f"Chemin demandé: {path}")
                    
                    clean_path = path.lstrip('/')
                    parent_folder = os.path.dirname(clean_path) if '/' in clean_path else ''
                    
                    app.logger.info(f"Chemin nettoyé: {clean_path}")
                    app.logger.info(f"Dossier parent: {parent_folder}")
                    
                    if parent_folder not in folders:
                        folders[parent_folder] = []
                    
                    full_path = os.path.join(temp_dir, clean_path)
                    app.logger.info(f"Chemin complet: {full_path}")
                    
                    try:
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        file.save(full_path)
                        app.logger.info(f"Fichier sauvegardé: {full_path}")
                    except Exception as e:
                        app.logger.error(f"Erreur lors de la sauvegarde du fichier {full_path}: {str(e)}")
                        raise
                    
                    file_size = os.path.getsize(full_path)
                    total_size += file_size
                    app.logger.info(f"Taille du fichier: {file_size} bytes")
                    
                    file_info = {
                        'name': clean_path,
                        'size': file_size,
                        'folder': parent_folder
                    }
                    folders[parent_folder].append(file_info)
                    file_list.append(file_info)
            
            app.logger.info("=== CRÉATION DU ZIP ===")
            zip_filename = f"transfer_{file_id}.zip"
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            app.logger.info(f"Nom du ZIP: {zip_filename}")
            app.logger.info(f"Chemin du ZIP: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        app.logger.info(f"Ajout au ZIP: {file_path} -> {arcname}")
                        zipf.write(file_path, arcname)
            
            app.logger.info("ZIP créé avec succès")
            
            with open(zip_path, 'rb') as f:
                encrypted_data = hashlib.sha256(f.read()).hexdigest()
            app.logger.info(f"Hash du ZIP: {encrypted_data}")
            
            app.logger.info("=== ENREGISTREMENT EN BASE ===")
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
            app.logger.info("Enregistrement en base réussi")
            
        except Exception as e:
            app.logger.error(f"Erreur lors du traitement des fichiers: {str(e)}")
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                app.logger.info(f"Nettoyage: dossier temporaire supprimé {temp_dir}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
                app.logger.info(f"Nettoyage: fichier ZIP supprimé {zip_path}")
            return jsonify({'error': 'Erreur lors du traitement des fichiers'}), 500
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                app.logger.info(f"Nettoyage final: dossier temporaire supprimé {temp_dir}")

        app.logger.info("=== PRÉPARATION DES NOTIFICATIONS ===")
        files_summary = []
        for folder, files in folders.items():
            if folder:
                files_summary.append(f"\nDossier {folder}:")
            for f in files:
                prefix = "  " if folder else ""
                files_summary.append(f"{prefix}- {os.path.basename(f['name'])} ({format_size(f['size'])})")
        
        files_summary = "\n".join(files_summary)
        total_size_formatted = format_size(total_size)
        app.logger.info(f"Résumé des fichiers préparé: \n{files_summary}")
        app.logger.info(f"Taille totale: {total_size_formatted}")

        app.logger.info("=== ENVOI DES NOTIFICATIONS ===")
        try:
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)
                app.logger.info(f"Configuration SMTP chargée depuis {app.config['SMTP_CONFIG_PATH']}")
        except Exception as e:
            app.logger.error(f"Erreur lors du chargement de la configuration SMTP: {str(e)}")
            return jsonify({'error': 'Erreur de configuration SMTP'}), 500

        notification_errors = []
        
        zip_name = zip_filename
        app.logger.info(f"Envoi de la notification au destinataire: {email}")
        if not send_recipient_notification_with_files(email, file_id, zip_name, files_summary, total_size_formatted, smtp_config):
            app.logger.error(f"Échec de l'envoi au destinataire: {email}")
            notification_errors.append("destinataire")
        
        app.logger.info(f"Envoi de la confirmation à l'expéditeur: {sender_email}")
        if not send_sender_upload_confirmation_with_files(sender_email, file_id, zip_name, files_summary, total_size_formatted, smtp_config):
            app.logger.error(f"Échec de l'envoi à l'expéditeur: {sender_email}")
            notification_errors.append("expéditeur")

        response_data = {
            'success': True,
            'file_id': file_id,
            'message': 'Fichiers uploadés avec succès'
        }

        if notification_errors:
            warning_msg = f"Impossible d'envoyer les notifications aux destinataires suivants: {', '.join(notification_errors)}"
            app.logger.warning(warning_msg)
            response_data['warning'] = warning_msg

        app.logger.info("=== UPLOAD TERMINÉ AVEC SUCCÈS ===")
        return jsonify(response_data), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload: {str(e)}")
        app.logger.error(f"Traceback complet: {traceback.format_exc()}")
        if 'zip_path' in locals() and os.path.exists(zip_path):
            os.remove(zip_path)
            app.logger.info(f"Nettoyage d'erreur: fichier ZIP supprimé {zip_path}")
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
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_upload.filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        if not file_upload.downloaded:
            file_upload.downloaded = True
            db.session.commit()
            
            try:
                with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                    smtp_config = json.load(config_file)
                send_sender_download_notification(file_upload.sender_email, file_upload.filename, smtp_config)
            except Exception as e:
                app.logger.error(f"Erreur lors de l'envoi de la notification de téléchargement: {str(e)}")

        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_upload.filename
        )

    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement: {str(e)}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

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

def format_size(size):
    """Formate la taille en bytes en une chaîne lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
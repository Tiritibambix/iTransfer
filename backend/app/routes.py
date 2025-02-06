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
import zipfile
import shutil
from datetime import datetime, timedelta
import pytz
import schedule
import time
import threading

def format_size(bytes):
    """
    Formate une taille en bytes en une chaîne lisible (KB, MB, GB, etc.)
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"

def send_email_with_smtp(msg, smtp_config):
    """
    Envoie un email en utilisant le mode de connexion approprié selon le port SMTP
    """
    server = None
    try:
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
        
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
        server.send_message(msg)
        return True
        
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        return False
        
    finally:
        if server:
            try:
                server.quit()
            except Exception as e:
                app.logger.error(f"Erreur lors de la fermeture de la connexion SMTP : {str(e)}")

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

def create_email_template(title, message, file_summary, total_size, download_link=None):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #170017;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                padding: 0;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}
            .header {{
                text-align: center;
                padding: 30px 0;
                background: #693a67;
                border-radius: 12px 12px 0 0;
                margin-bottom: 0;
            }}
            .header h1 {{
                color: #ffffff;
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            .content {{
                padding: 30px;
                background-color: #ffffff;
            }}
            .message {{
                margin-bottom: 30px;
            }}
            .message h2 {{
                color: #693a67;
                margin: 0 0 15px 0;
                font-size: 22px;
                font-weight: 500;
            }}
            .message p {{
                color: #170017;
                margin: 0;
                font-size: 16px;
                line-height: 1.6;
            }}
            .files {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                color: #170017;
                border: 1px solid rgba(0, 0, 0, 0.05);
                margin: 20px 0;
            }}
            .total {{
                margin-top: 20px;
                padding: 15px 20px;
                background-color: #693a67;
                color: #ffffff;
                border-radius: 8px;
                font-weight: 500;
                font-size: 16px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #5a4e5a;
                font-size: 14px;
                border-top: 1px solid rgba(0, 0, 0, 0.05);
            }}
            .download-btn {{
                display: inline-block;
                margin: 20px 0;
                padding: 12px 24px;
                background-color: #693a67;
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                text-align: center;
            }}
            .download-btn:hover {{
                background-color: #7e547b;
            }}
            .link {{
                color: #693a67;
                text-decoration: none;
            }}
            .link:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>iTransfer</h1>
            </div>
            <div class="content">
                <div class="message">
                    <h2>{title}</h2>
                    <p>{message}</p>
                </div>
                {f'<a href="{download_link}" class="download-btn">Télécharger les fichiers</a>' if download_link else ''}
                <div class="files">
{file_summary}
                </div>
                <div class="total">
                    {total_size}
                </div>
            </div>
            <div class="footer">
                <p>Envoyé via iTransfer</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Version texte brut pour les clients qui ne supportent pas l'HTML
    text = f"""
{title}

{message}

{f'Lien de téléchargement : {download_link}' if download_link else ''}

Résumé des fichiers :
{file_summary}

Taille totale : {total_size}

Envoyé via iTransfer
    """
    
    return html, text

def send_recipient_notification_with_files(recipient_email, file_id, file_name, files_summary, total_size, smtp_config, sender_email):
    """
    Envoie un email de notification au destinataire avec le résumé des fichiers
    """
    try:
        # Récupérer les informations du fichier pour avoir la date d'expiration
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            app.logger.error(f"Fichier non trouvé pour l'envoi de notification: {file_id}")
            return False

        # Formater la date d'expiration dans le fuseau horaire configuré
        timezone = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        expiration_date = file_info.expires_at.astimezone(timezone)
        expiration_formatted = expiration_date.strftime('%d/%m/%Y à %H:%M:%S')

        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"
        app.logger.info(f"Lien de téléchargement généré : {download_link}")

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = recipient_email
        msg['Subject'] = f"{sender_email} vous envoie des fichiers"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        title = "Vous avez reçu des fichiers"
        message = f"""{sender_email} vous a envoyé des fichiers.<br><br>Ce lien expirera le {expiration_formatted}"""

        html, text = create_email_template(title, message, files_summary, total_size, download_link)
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de l'email : {str(e)}")
        return False

def send_sender_upload_confirmation_with_files(sender_email, file_id, file_name, files_summary, total_size, smtp_config, recipient_email):
    """
    Envoie un email de confirmation à l'expéditeur avec le résumé des fichiers envoyés
    """
    try:
        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"
        app.logger.info(f"Lien de téléchargement généré : {download_link}")

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Subject'] = f"Confirmation de votre transfert de fichiers à {recipient_email}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        title = "Vos fichiers ont été envoyés"
        message = f"""Vos fichiers ont été envoyés avec succès à : {recipient_email}<br><br>Lien de téléchargement : {download_link}"""

        html, text = create_email_template(title, message, files_summary, total_size)
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de l'email : {str(e)}")
        return False

def send_download_notification(sender_email, file_id, smtp_config):
    try:
        # Récupérer le fuseau horaire configuré
        timezone = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        # Obtenir l'heure actuelle dans le bon fuseau horaire
        download_time = datetime.now(timezone).strftime('%d/%m/%Y à %H:%M:%S (%Z)')
        
        # Récupérer les informations du fichier
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            app.logger.error(f"Fichier non trouvé pour l'envoi de notification: {file_id}")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Vos fichiers ont été téléchargés"
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        # Récupérer la liste des fichiers depuis la base de données
        files_summary = ""
        total_size = 0
        if file_info.files_list:
            try:
                files_data = json.loads(file_info.files_list)
                for file_data in files_data:
                    files_summary += f"- {file_data['name']} ({format_size(file_data['size'])})\n"
                    total_size += file_data['size']
                total_size = format_size(total_size)
            except Exception as e:
                app.logger.error(f"Erreur lors de la lecture de la liste des fichiers: {str(e)}")
                files_summary = f"- {file_info.filename}"
                total_size = "Taille non disponible"
        else:
            files_summary = f"- {file_info.filename}"
            total_size = "Taille non disponible"

        title = "Vos fichiers ont été téléchargés"
        message = f"Vos fichiers ont été téléchargés le {download_time}."

        html, text = create_email_template(title, message, files_summary, total_size)
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de la notification de téléchargement: {str(e)}")
        return False

def cleanup_expired_files():
    try:
        # Récupérer tous les fichiers expirés
        expired_files = FileUpload.query.filter(FileUpload.expires_at < datetime.now()).all()
        
        for file in expired_files:
            try:
                # Supprimer le fichier physique
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f"Fichier expiré supprimé: {file_path}")
                
                # Supprimer l'entrée de la base de données
                db.session.delete(file)
                app.logger.info(f"Entrée de base de données supprimée pour le fichier: {file.id}")
            except Exception as e:
                app.logger.error(f"Erreur lors de la suppression du fichier {file.id}: {str(e)}")
        
        db.session.commit()
        app.logger.info("Nettoyage des fichiers expirés terminé")
    except Exception as e:
        app.logger.error(f"Erreur lors du nettoyage des fichiers expirés: {str(e)}")

def run_scheduler():
    schedule.every(12).hours.do(cleanup_expired_files)
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Attendre 1 heure

# Démarrer le scheduler dans un thread séparé
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Vérifier que tous les champs requis sont présents
        if not all(field in request.form for field in ['recipientEmail', 'senderEmail', 'expirationDays']):
            return jsonify({'error': 'Champs manquants'}), 400

        recipient_email = request.form['recipientEmail']
        sender_email = request.form['senderEmail']
        expiration_days = int(request.form['expirationDays'])
        
        # Vérifier qu'il y a au moins un fichier
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        files = request.files.getlist('file')
        if not files or not files[0].filename:
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400

        # Générer un ID unique pour ce transfert
        transfer_id = str(uuid.uuid4())
        
        # Créer le dossier d'upload s'il n'existe pas
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Préparer la liste des fichiers pour le stockage
        files_info = []
        total_size = 0

        # Si c'est un seul fichier, pas besoin de ZIP
        if len(files) == 1 and '/' not in files[0].filename:
            file = files[0]
            safe_filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, safe_filename)
            file.save(file_path)
            
            # Stocker les informations du fichier
            file_size = os.path.getsize(file_path)
            files_info.append({
                'name': safe_filename,
                'size': file_size
            })
            total_size = file_size
            final_filename = safe_filename
        else:
            # Créer un fichier ZIP pour plusieurs fichiers
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'transfer_{timestamp}.zip'
            zip_path = os.path.join(upload_folder, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    # Sécuriser le nom du fichier
                    safe_filename = secure_filename(file.filename)
                    
                    # Sauvegarder temporairement le fichier
                    temp_path = os.path.join(upload_folder, safe_filename)
                    file.save(temp_path)
                    
                    # Ajouter au ZIP
                    zipf.write(temp_path, safe_filename)
                    
                    # Récupérer la taille et stocker les infos
                    file_size = os.path.getsize(temp_path)
                    files_info.append({
                        'name': safe_filename,
                        'size': file_size
                    })
                    total_size += file_size
                    
                    # Supprimer le fichier temporaire
                    os.remove(temp_path)
            
            final_filename = zip_filename

        # Calculer la date d'expiration
        expiration_date = datetime.now() + timedelta(days=expiration_days)
        
        # Créer l'entrée dans la base de données
        file_upload = FileUpload(
            id=transfer_id,
            filename=final_filename,
            email=recipient_email,
            sender_email=sender_email,
            encrypted_data='',  # Non utilisé pour le moment
            expires_at=expiration_date,
            files_list=json.dumps(files_info)  # Stocker la liste des fichiers en JSON
        )
        
        db.session.add(file_upload)
        db.session.commit()

        # Préparer le résumé des fichiers
        files_summary = ""
        for file_info in files_info:
            files_summary += f"- {file_info['name']} ({format_size(file_info['size'])})\n"
        files_summary += f"\nTaille totale : {format_size(total_size)}"

        # Envoyer les notifications
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)

        notification_errors = []

        try:
            if not send_recipient_notification_with_files(recipient_email, transfer_id, final_filename, files_summary, format_size(total_size), smtp_config, sender_email):
                app.logger.error(f"Échec de l'envoi de la notification au destinataire: {recipient_email}")
                notification_errors.append("destinataire")
            
            if not send_sender_upload_confirmation_with_files(sender_email, transfer_id, final_filename, files_summary, format_size(total_size), smtp_config, recipient_email):
                app.logger.error(f"Échec de l'envoi de la notification à l'expéditeur: {sender_email}")
                notification_errors.append("expéditeur")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")

        response_data = {
            'success': True,
            'file_id': transfer_id,
            'message': 'Fichiers uploadés avec succès'
        }

        if notification_errors:
            response_data['notification_errors'] = notification_errors
            response_data['message'] += f" (Échec de l'envoi des notifications: {', '.join(notification_errors)})"

        return jsonify(response_data), 201

    except Exception as e:
        app.logger.error(f"Erreur lors du traitement des fichiers: {str(e)}")
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        # Récupérer les informations du fichier depuis la base de données
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            app.logger.error(f"Fichier non trouvé: {file_id}")
            return jsonify({'error': 'Fichier non trouvé'}), 404

        # Vérifier l'expiration
        if datetime.now() > file_info.expires_at:
            app.logger.info(f"Tentative d'accès à un fichier expiré: {file_id}")
            return jsonify({'error': 'Le lien de téléchargement a expiré'}), 410

        # Construire le chemin du fichier
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info.filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404

        # Marquer le fichier comme téléchargé
        if not file_info.downloaded:
            file_info.downloaded = True
            db.session.commit()

            # Charger la configuration SMTP
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)

            # Récupérer la liste des fichiers depuis la base de données
            files_summary = ""
            total_size = 0
            if file_info.files_list:
                try:
                    files_data = json.loads(file_info.files_list)
                    for file_data in files_data:
                        files_summary += f"- {file_data['name']} ({format_size(file_data['size'])})\n"
                        total_size += file_data['size']
                    total_size = format_size(total_size)
                except Exception as e:
                    app.logger.error(f"Erreur lors de la lecture de la liste des fichiers: {str(e)}")
                    files_summary = f"- {file_info.filename}"
                    total_size = "Taille non disponible"
            else:
                files_summary = f"- {file_info.filename}"
                total_size = "Taille non disponible"

            # Envoyer une notification à l'expéditeur
            send_download_notification(file_info.sender_email, file_id, smtp_config)

        # Envoyer le fichier
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_info.filename)
        )

    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors du téléchargement'}), 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight success'}), 200

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
        # Ici, vous pourriez vouloir générer un vrai token JWT
        token = "admin-token"  # Simplifié pour l'exemple
        return jsonify({'token': token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/save-smtp-settings', methods=['POST'])
def save_smtp_settings():
    """
    Sauvegarde la configuration SMTP
    """
    try:
        app.logger.info("Réception d'une nouvelle configuration SMTP")
        data = request.get_json()
        
        # Validation des données requises
        required_fields = ['smtpServer', 'smtpPort', 'smtpUser', 'smtpPassword', 'smtpSenderEmail']
        for field in required_fields:
            if not data.get(field):
                app.logger.error(f"Champ manquant : {field}")
                return jsonify({'error': f'Le champ {field} est requis'}), 400

        # Formater la configuration
        smtp_config = {
            'smtp_server': data['smtpServer'],
            'smtp_port': data['smtpPort'],
            'smtp_user': data['smtpUser'],
            'smtp_password': data['smtpPassword'],
            'smtp_sender_email': data['smtpSenderEmail']
        }

        app.logger.info("Configuration SMTP reçue et sauvegardée (détails non inclus pour des raisons de sécurité)")
        
        # Sauvegarder la configuration
        with open(app.config['SMTP_CONFIG_PATH'], 'w') as config_file:
            json.dump(smtp_config, config_file, indent=2)
        
        app.logger.info("Configuration SMTP sauvegardée avec succès")
        return jsonify({'message': 'Configuration SMTP sauvegardée'}), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de la sauvegarde de la configuration SMTP : {str(e)}")
        return jsonify({'error': 'Une erreur interne est survenue lors de la sauvegarde.'}), 500

@app.route('/api/test-smtp', methods=['POST'])
def test_smtp():
    """
    Teste la configuration SMTP en envoyant un email de test
    """
    try:
        app.logger.info("Début du test SMTP")
        
        # Charger la configuration SMTP
        try:
            with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
                smtp_config = json.load(config_file)
                app.logger.info(f"Configuration SMTP chargée : serveur={smtp_config['smtp_server']}, port={smtp_config['smtp_port']}, user={smtp_config['smtp_user']}, sender={smtp_config['smtp_sender_email']}")
        except Exception as e:
            app.logger.error(f"Erreur lors du chargement de la configuration SMTP : {str(e)}")
            return jsonify({'error': 'Configuration SMTP non trouvée. Veuillez d\'abord configurer les paramètres SMTP.'}), 404

        # Créer un message de test
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("iTransfer", smtp_config['smtp_sender_email']))
            msg['To'] = smtp_config['smtp_sender_email']
            msg['Subject'] = "Test de configuration SMTP"
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()

            text = "Ceci est un message de test pour vérifier la configuration SMTP."
            html = f"""
            <html>
              <body>
                <p>Ceci est un message de test pour vérifier la configuration SMTP.</p>
                <p>Si vous recevez ce message, la configuration SMTP est correcte.</p>
              </body>
            </html>
            """

            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            app.logger.info("Message de test créé avec succès")

        except Exception as e:
            app.logger.error(f"Erreur lors de la création du message de test : {str(e)}")
            return jsonify({'error': 'Erreur lors de la création du message.'}), 500

        # Tenter d'envoyer l'email
        if send_email_with_smtp(msg, smtp_config):
            app.logger.info("Test SMTP réussi")
            return jsonify({'message': 'Test SMTP réussi! Un email de test a été envoyé.'}), 200
        else:
            app.logger.error("Échec de l'envoi du message de test")
            return jsonify({'error': 'Échec du test SMTP. Vérifiez les logs pour plus de détails.'}), 500

    except Exception as e:
        app.logger.error(f"Erreur inattendue lors du test SMTP : {str(e)}")
        return jsonify({'error': 'Une erreur interne est survenue lors du test SMTP.'}), 500

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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                white-space: pre-wrap;
                color: #170017;
                border: 1px solid rgba(0, 0, 0, 0.05);
                margin: 20px 0;
                line-height: 1.8;
                font-size: 15px;
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

        # Obtenir l'URL frontend depuis la variable d'environnement
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500')
        download_page_link = f"{frontend_url}/download/{file_id}"
        app.logger.info(f"Lien vers la page de téléchargement généré : {download_page_link}")

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = recipient_email
        msg['Subject'] = f"{sender_email} vous envoie des fichiers"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        title = "Vous avez reçu des fichiers"
        message = f"""{sender_email} vous a envoyé des fichiers. Cliquez sur le bouton ci-dessous pour accéder à la page de téléchargement.<br><br>Ce lien expirera le {expiration_formatted}"""

        html, text = create_email_template(title, message, files_summary, total_size, download_page_link)
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de l'email : {str(e)}")
        return False

def send_sender_upload_confirmation_with_files(sender_email, file_id, file_name, files_list, total_size, smtp_config, recipient_email):
    """
    Envoie un email de confirmation à l'expéditeur avec le résumé des fichiers envoyés
    """
    try:
        # Obtenir l'URL frontend depuis la variable d'environnement
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500')
        download_page_link = f"{frontend_url}/download/{file_id}"
        app.logger.info(f"Lien vers la page de téléchargement généré : {download_page_link}")

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Subject'] = f"Confirmation de votre transfert de fichiers à {recipient_email}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        # Préparer le résumé des fichiers
        files_summary = ""
        for file_info in files_list:
            files_summary += f"- {file_info['name']} ({format_size(file_info['size'])})\n"

        title = "Vos fichiers ont été envoyés"
        message = f"""Vos fichiers ont été envoyés avec succès à : {recipient_email}<br><br>Vous pouvez accéder à la page de téléchargement ici : {download_page_link}"""

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

        # Récupérer la liste des fichiers et préparer le résumé
        files_list = file_info.get_files_list()
        if not files_list:
            # Si pas de liste stockée, utiliser le fichier final
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info.filename)
            file_size = os.path.getsize(file_path)
            files_summary = f"- {file_info.filename} ({format_size(file_size)})"
            total_size_formatted = format_size(file_size)
        else:
            # Utiliser la liste complète des fichiers
            total_size = 0
            files_summary = ""
            for f in files_list:
                files_summary += f"- {f['name']} ({format_size(f['size'])})\n"
                total_size += f['size']
            total_size_formatted = format_size(total_size)

        title = "Vos fichiers ont été téléchargés"
        message = f"Vos fichiers ont été téléchargés le {download_time}."

        html, text = create_email_template(title, message, files_summary, total_size_formatted)
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de la notification de téléchargement: {str(e)}")
        return False

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight success'}), 200

    try:
        app.logger.info("Début du traitement de l'upload")
        app.logger.info(f"Files in request: {request.files}")
        app.logger.info(f"Form data: {request.form}")
        
        if 'files[]' not in request.files:
            app.logger.error("Pas de fichiers dans la requête")
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')
        expiration_days = int(request.form.get('expiration_days', '7'))
        
        # Valider la durée d'expiration
        if expiration_days not in [3, 5, 7, 10]:
            expiration_days = 7  # Valeur par défaut si invalide
            
        app.logger.info(f"Durée d'expiration choisie: {expiration_days} jours")
        
        if not email or not sender_email:
            return jsonify({'error': 'Email addresses are required'}), 400

        # Récupérer et valider la liste des fichiers
        files_list = json.loads(request.form.get('files_list', '[]'))
        if not files_list:
            return jsonify({'error': 'Liste des fichiers invalide'}), 400

        # Calculer la taille totale pour affichage
        total_size = sum(file_info['size'] for file_info in files_list)
        total_size_mb = total_size / (1024 * 1024)

        # Préparer le contenu des fichiers pour les emails
        files_content = ""
        for file_info in files_list:
            size_mb = file_info['size'] / (1024 * 1024)
            files_content += f"- {file_info['name']} ({format_size(file_info['size'])})\n"

        # Sauvegarder les fichiers
        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)
        app.logger.info(f"Dossier temporaire créé: {temp_dir}")

        folders = {}
        file_list = []

        # Sauvegarder les fichiers avec leur structure de dossiers
        for file, path in zip(files, paths):
            if file.filename:
                # Nettoyer le chemin et extraire le dossier parent
                clean_path = path.lstrip('/')
                # S'assurer qu'il n'y a qu'un seul niveau de dossier
                path_parts = clean_path.split('/')
                if len(path_parts) > 1:
                    parent_folder = path_parts[0]
                    filename = path_parts[-1]
                    clean_path = f"{parent_folder}/{filename}" if parent_folder else filename
                else:
                    parent_folder = ''
                    
                if parent_folder not in folders:
                    folders[parent_folder] = []
                
                # Créer le dossier temporaire si nécessaire
                temp_file_path = os.path.join(temp_dir, clean_path)
                if parent_folder:
                    os.makedirs(os.path.join(temp_dir, parent_folder), exist_ok=True)
                    app.logger.info(f"Création du dossier: {os.path.join(temp_dir, parent_folder)}")
                
                # Sauvegarder le fichier
                file.save(temp_file_path)
                app.logger.info(f"Fichier sauvegardé: {temp_file_path}")
                
                file_size = os.path.getsize(temp_file_path)
                app.logger.info(f"Taille du fichier: {format_size(file_size)}")
                
                # Ajouter à la liste des fichiers avec la structure correcte
                file_info = {
                    'name': clean_path,
                    'size': file_size,
                    'folder': parent_folder,
                    'temp_path': temp_file_path
                }
                folders[parent_folder].append(file_info)
                file_list.append(file_info)

        # Déterminer si on doit créer un zip
        needs_zip = len(file_list) > 1 or any(f['folder'] for f in file_list)
        
        if needs_zip:
            # Créer le ZIP avec la même structure
            # Créer un nom de fichier avec la date et l'heure
            now = datetime.now()
            date_str = now.strftime("%y%m%d%H%M")
            final_filename = f"iTransfer_{date_str}.zip"
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
            app.logger.info(f"Création du ZIP: {zip_path}")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for parent_folder, folder_files in folders.items():
                    for file_info in folder_files:
                        app.logger.info(f"Ajout au ZIP: {file_info['name']}")
                        # Utiliser le nom nettoyé pour l'archivage
                        zipf.write(file_info['temp_path'], file_info['name'])

            # Hasher le fichier zip
            with open(zip_path, 'rb') as f:
                encrypted_data = hashlib.sha256(f.read()).hexdigest()
            
            final_path = zip_path
        else:
            # Cas d'un fichier unique
            single_file = file_list[0]
            final_filename = single_file['name']
            final_path = single_file['temp_path']
            
            # Hasher le fichier unique
            with open(final_path, 'rb') as f:
                encrypted_data = hashlib.sha256(f.read()).hexdigest()
            
            # Déplacer le fichier vers le dossier final
            final_destination = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
            shutil.move(final_path, final_destination)
            final_path = final_destination

        app.logger.info(f"Hash du fichier: {encrypted_data}")

        # Préparer la liste des fichiers initiale avec les tailles et noms originaux
        original_files = []
        for file_info in files_list:
            original_files.append({
                'name': file_info['name'],
                'size': file_info['size']
            })

        # Sauvegarder en base avec la liste des fichiers originaux
        # Créer l'entrée en base avec la liste des fichiers originaux
        new_file = FileUpload(
            id=file_id,
            filename=final_filename,
            email=email,
            sender_email=sender_email,
            encrypted_data=encrypted_data,
            downloaded=False,
            expires_at=datetime.now() + timedelta(days=expiration_days)
        )
        new_file.set_files_list(original_files)
        db.session.add(new_file)
        db.session.commit()
        app.logger.info(f"Fichier enregistré en base avec l'ID: {file_id}")

        # Préparer le résumé des fichiers à partir des données brutes
        files_summary = ""
        for file_info in files_list:
            files_summary += f"- {file_info['name']} ({format_size(file_info['size'])})\n"
        total_size_formatted = format_size(total_size)

        # Envoyer les notifications
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)

        notification_errors = []

        try:
            # Récupérer la liste des fichiers stockée pour les notifications
            stored_files = new_file.get_files_list()
            files_summary = ""
            for file_info in stored_files:
                files_summary += f"- {file_info['name']} ({format_size(file_info['size'])})\n"

            if not send_recipient_notification_with_files(email, file_id, final_filename, files_summary, total_size_formatted, smtp_config, sender_email):
                app.logger.error(f"Échec de l'envoi de la notification au destinataire: {email}")
                notification_errors.append("destinataire")
            
            if not send_sender_upload_confirmation_with_files(sender_email, file_id, final_filename, stored_files, total_size_formatted, smtp_config, email):
                app.logger.error(f"Échec de l'envoi de la notification à l'expéditeur: {sender_email}")
                notification_errors.append("expéditeur")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi des emails : {str(e)}")
            notification_errors.append("tous les destinataires")

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
        app.logger.error(f"Erreur lors du traitement des fichiers: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if 'zip_path' in locals() and os.path.exists(zip_path):
            os.remove(zip_path)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

    finally:
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.route('/transfer/<file_id>', methods=['GET'])
def get_transfer_details(file_id):
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

        # Récupérer la liste des fichiers stockée
        files_list = file_info.get_files_list()
        
        if not files_list:
            # Si pas de liste stockée, vérifier si le fichier existe
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info.filename)
            if not os.path.exists(file_path):
                return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404
                
            # Créer une liste avec le fichier unique
            file_size = os.path.getsize(file_path)
            files_list = [{
                'name': file_info.filename,
                'size': file_size
            }]
        else:
            # Vérifier si le fichier final existe (ZIP ou fichier unique)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info.filename)
            if not os.path.exists(file_path):
                return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404

        # Retourner la liste des fichiers avec les détails
        return jsonify({
            'files': files_list,
            'expires_at': file_info.expires_at.isoformat()
        }), 200

    except Exception as e:
        app.logger.error(f"Erreur lors de la récupération des détails : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue'}), 500

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
            files_list = file_info.get_files_list()
            
            # Préparer le résumé des fichiers
            total_size = 0
            files_summary = ""
            
            if files_list:
                for f in files_list:
                    files_summary += f"- {f['name']} ({format_size(f['size'])})\n"
                    total_size += f['size']
                total_size_formatted = format_size(total_size)
            else:
                # Fallback pour un seul fichier
                file_size = os.path.getsize(file_path)
                files_summary = f"- {file_info.filename} ({format_size(file_size)})"
                total_size_formatted = format_size(file_size)

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

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
from datetime import datetime
import pytz

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
        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"
        app.logger.info(f"Lien de téléchargement généré : {download_link}")

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = recipient_email
        msg['Subject'] = f"{sender_email}: Nouveau transfert de fichiers."
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        title = "Vous avez reçu des fichiers"
        message = f"""
{sender_email} vous a envoyé des fichiers.

Vous pouvez les télécharger en cliquant ici :"""

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
        message = f"""
Vos fichiers ont été envoyés avec succès à :
{recipient_email}

Lien de téléchargement : <a href="{download_link}" class="link">{download_link}</a>"""

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
        
        files_info = app.config.get(f'files_summary_{file_id}', {})
        files_summary = files_info.get('summary', 'Information non disponible')
        total_size = files_info.get('total_size', 'Taille non disponible')

        subject = "Vos fichiers ont été téléchargés"
        body = f"""Bonjour,

Vos fichiers ont été téléchargés le {download_time}.

Fichiers téléchargés :
{files_summary}

Cordialement,
L'équipe iTransfer"""

        return send_email(sender_email, subject, body, smtp_config)
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
        
        if not email or not sender_email:
            return jsonify({'error': 'Email addresses are required'}), 400

        # Récupérer la liste des fichiers pour les emails
        files_list = json.loads(request.form.get('files_list', '[]'))
        
        # Préparer le contenu des fichiers pour les emails
        files_content = ""
        total_size = 0
        for file_info in files_list:
            size_mb = file_info['size'] / (1024 * 1024)
            files_content += f"- {file_info['name']} ({size_mb:.2f} MB)\n"
            total_size += file_info['size']
        
        total_size_mb = total_size / (1024 * 1024)
        files_content += f"\nTaille totale : {total_size_mb:.2f} MB"

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
            final_filename = f"transfer_{file_id}.zip"
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

        # Sauvegarder en base
        new_file = FileUpload(
            id=file_id,
            filename=final_filename,
            email=email,
            sender_email=sender_email,
            encrypted_data=encrypted_data,
            downloaded=False
        )
        db.session.add(new_file)
        db.session.commit()
        app.logger.info(f"Fichier enregistré en base avec l'ID: {file_id}")

        # Préparer le résumé des fichiers
        files_summary = files_content
        
        # Stocker le résumé pour l'email de confirmation de téléchargement
        app.config[f'files_summary_{file_id}'] = {
            'summary': files_summary,
            'total_size': f"{total_size_mb:.2f} MB"
        }

        # Envoyer les notifications
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)

        notification_errors = []

        try:
            if not send_recipient_notification_with_files(email, file_id, final_filename, files_summary, f"{total_size_mb:.2f} MB", smtp_config, sender_email):
                app.logger.error(f"Échec de l'envoi de la notification au destinataire: {email}")
                notification_errors.append("destinataire")
            
            if not send_sender_upload_confirmation_with_files(sender_email, file_id, final_filename, files_summary, f"{total_size_mb:.2f} MB", smtp_config, email):
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

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        # Récupérer les informations du fichier depuis la base de données
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            return jsonify({'error': 'Fichier non trouvé'}), 404

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

            # Récupérer le résumé des fichiers stocké lors de l'upload
            stored_summary = app.config.get(f'files_summary_{file_id}')
            if stored_summary:
                files_summary = stored_summary['summary']
                total_size_formatted = stored_summary['total_size']
                # Nettoyer après utilisation
                del app.config[f'files_summary_{file_id}']
            else:
                # Fallback si le résumé n'est pas trouvé
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

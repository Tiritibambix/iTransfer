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

def send_recipient_notification_with_files(recipient_email, file_id, zip_filename, files_summary, total_size, smtp_config):
    """
    Envoie un email de notification au destinataire avec le résumé des fichiers
    """
    try:
        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"
        app.logger.info(f"Lien de téléchargement généré : {download_link}")

        msg = MIMEMultipart()
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = recipient_email
        msg['Subject'] = "Nouveau transfert de fichiers reçu"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        body = f"""
        Bonjour,

        Vous avez reçu un nouveau transfert de fichiers.

        Résumé des fichiers :
        {files_summary}

        Taille totale : {total_size}

        Lien de téléchargement : {download_link}
        Ce lien expirera dans 7 jours.

        Cordialement,
        L'équipe iTransfer
        """

        msg.attach(MIMEText(body, 'plain'))
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de l'email : {str(e)}")
        return False

def send_sender_upload_confirmation_with_files(sender_email, file_id, zip_filename, files_summary, total_size, smtp_config):
    """
    Envoie un email de confirmation à l'expéditeur avec le résumé des fichiers envoyés
    """
    try:
        backend_url = get_backend_url()
        download_link = f"{backend_url}/download/{file_id}"
        app.logger.info(f"Lien de téléchargement généré : {download_link}")

        msg = MIMEMultipart()
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Subject'] = "Confirmation de votre transfert de fichiers"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        body = f"""
        Bonjour,

        Votre transfert de fichiers a été effectué avec succès.

        Résumé des fichiers envoyés :
        {files_summary}

        Taille totale : {total_size}
        
        Lien de téléchargement : {download_link}
        Ce lien expirera dans 7 jours.

        Une notification a été envoyée au destinataire avec ce même lien.

        Cordialement,
        L'équipe iTransfer
        """

        msg.attach(MIMEText(body, 'plain'))
        return send_email_with_smtp(msg, smtp_config)
    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de l'email : {str(e)}")
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
        
        # Ajout de logs pour déboguer le contenu du form
        app.logger.info(f"Contenu du form data: {request.form}")
        
        # Récupérer les emails avec vérification des deux formats possibles
        email = request.form.get('recipientEmail') or request.form.get('email')
        sender_email = request.form.get('senderEmail') or request.form.get('sender_email')
        
        # Log plus détaillé des valeurs
        app.logger.info(f"Nombre de fichiers: {len(files)}")
        app.logger.info(f"Nombre de paths: {len(paths)}")
        app.logger.info(f"Email destinataire (recipientEmail/email): {email}")
        app.logger.info(f"Email expéditeur (senderEmail/sender_email): {sender_email}")

        if not files or not email or not sender_email:
            app.logger.error(f"Données manquantes - files: {bool(files)}, email: {bool(email)}, sender_email: {bool(sender_email)}")
            return jsonify({'error': 'Fichiers et emails requis'}), 400

        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)
        app.logger.info(f"Dossier temporaire créé: {temp_dir}")

        total_size = 0
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
                total_size += file_size
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

        # Créer le ZIP avec la même structure
        zip_filename = f"transfer_{file_id}.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        app.logger.info(f"Création du ZIP: {zip_path}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for parent_folder, folder_files in folders.items():
                for file_info in folder_files:
                    app.logger.info(f"Ajout au ZIP: {file_info['name']}")
                    # Utiliser le nom nettoyé pour l'archivage
                    zipf.write(file_info['temp_path'], file_info['name'])

        # Hasher le fichier
        with open(zip_path, 'rb') as f:
            encrypted_data = hashlib.sha256(f.read()).hexdigest()
        app.logger.info(f"Hash du ZIP: {encrypted_data}")

        # Sauvegarder en base
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
        app.logger.info(f"Fichier enregistré en base avec l'ID: {file_id}")

        # Préparer le résumé des fichiers
        files_summary = []
        for f in file_list:
            files_summary.append(f"- {f['name']} ({format_size(f['size'])})")
        
        files_summary = "\n".join(files_summary)
        total_size_formatted = format_size(total_size)
        app.logger.info(f"Résumé des fichiers:\n{files_summary}\nTaille totale: {total_size_formatted}")

        # Vérification de zip_filename avant l'envoi des emails
        if 'zip_filename' not in locals():
            app.logger.error("zip_filename n'est pas défini avant l'envoi des emails")
            return jsonify({'error': 'Une erreur interne est survenue lors de la préparation du fichier'}), 500

        # Envoyer les notifications
        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)

        notification_errors = []

        try:
            if not send_recipient_notification_with_files(email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
                app.logger.error(f"Échec de l'envoi de la notification au destinataire: {email}")
                notification_errors.append("destinataire")
            
            if not send_sender_upload_confirmation_with_files(sender_email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
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

            # Envoyer une notification à l'expéditeur
            msg = MIMEMultipart()
            msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
            msg['To'] = file_info.sender_email
            msg['Subject'] = "Votre fichier a été téléchargé"
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()

            body = f"""
            Bonjour,

            Votre fichier {file_info.filename} a été téléchargé.

            Cordialement,
            L'équipe iTransfer
            """

            msg.attach(MIMEText(body, 'plain'))
            send_email_with_smtp(msg, smtp_config)

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

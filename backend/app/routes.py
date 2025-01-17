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
        email = request.form.get('recipientEmail')
        sender_email = request.form.get('senderEmail')

        app.logger.info(f"Nombre de fichiers: {len(files)}")
        app.logger.info(f"Nombre de paths: {len(paths)}")
        app.logger.info(f"Email destinataire: {email}")
        app.logger.info(f"Email expéditeur: {sender_email}")

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

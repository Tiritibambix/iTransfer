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
        if 'files[]' not in request.files:
            return jsonify({'error': 'Aucun fichier envoyé'}), 400
        
        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        email = request.form.get('recipientEmail')
        sender_email = request.form.get('senderEmail')

        if not files or not email or not sender_email:
            return jsonify({'error': 'Fichiers et emails requis'}), 400

        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)

        total_size = 0
        file_list = []
        folders = {}

        for file, path in zip(files, paths):
            if file.filename:
                # Nettoyer le chemin et extraire le dossier parent
                clean_path = path.lstrip('/')
                parent_folder = os.path.dirname(clean_path) if '/' in clean_path else ''
                
                if parent_folder not in folders:
                    folders[parent_folder] = []
                
                # Créer le dossier temporaire si nécessaire
                temp_file_path = os.path.join(temp_dir, clean_path)
                os.makedirs(os.path.dirname(temp_file_path) if os.path.dirname(temp_file_path) else temp_dir, exist_ok=True)
                
                # Sauvegarder le fichier
                file.save(temp_file_path)
                
                file_size = os.path.getsize(temp_file_path)
                total_size += file_size
                
                # Ajouter à la liste des fichiers avec la structure correcte
                file_info = {
                    'name': clean_path,
                    'size': file_size,
                    'folder': parent_folder,
                    'temp_path': temp_file_path
                }
                folders[parent_folder].append(file_info)
                file_list.append(file_info)
        
        zip_filename = f"transfer_{file_id}.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder_name, folder_files in folders.items():
                for file_info in folder_files:
                    arcname = file_info['name']
                    zipf.write(file_info['temp_path'], arcname)
        
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

        # Préparer un résumé des fichiers organisé par dossier
        files_summary = []
        for folder, files in folders.items():
            if folder:
                files_summary.append(f"\nDossier {folder}:")
            for f in files:
                prefix = "  " if folder else ""
                files_summary.append(f"{prefix}- {os.path.basename(f['name'])} ({format_size(f['size'])})")
        
        files_summary = "\n".join(files_summary)
        total_size_formatted = format_size(total_size)

        with open(app.config['SMTP_CONFIG_PATH'], 'r') as config_file:
            smtp_config = json.load(config_file)

        notification_errors = []
        
        if not send_recipient_notification_with_files(email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
            notification_errors.append("destinataire")
        
        if not send_sender_upload_confirmation_with_files(sender_email, file_id, zip_filename, files_summary, total_size_formatted, smtp_config):
            notification_errors.append("expéditeur")

        response_data = {
            'success': True,
            'file_id': file_id,
            'message': 'Fichiers uploadés avec succès'
        }

        if notification_errors:
            response_data['warning'] = f"Impossible d'envoyer les notifications aux destinataires suivants: {', '.join(notification_errors)}"

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

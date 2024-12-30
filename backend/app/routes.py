import os
import uuid
import hashlib
import smtplib
from flask import request, jsonify
from . import app, db
from .models import FileUpload

# Charger l'URL dynamique du backend (par exemple, pour envoyer des notifications)
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint pour recevoir un fichier et un email, les enregistrer et envoyer une notification.
    """
    try:
        # Récupérer le fichier et l'email depuis la requête
        file = request.files.get('file')
        email = request.form.get('email')

        # Valider les données
        if not file or not email:
            return jsonify({'error': 'Fichier et email sont requis'}), 400

        # Générer un identifiant unique pour l'upload
        file_id = str(uuid.uuid4())

        # Créer un hash du fichier (exemple d'encryptage)
        encrypted_data = hashlib.sha256(file.read()).hexdigest()

        # Enregistrer les données dans la base
        new_file = FileUpload(
            id=file_id,
            filename=file.filename,
            email=email,
            encrypted_data=encrypted_data,
        )
        db.session.add(new_file)
        db.session.commit()

        # Appeler un autre service si nécessaire (exemple : notification)
        notify_user(file_id, email)

        return jsonify({'file_id': file_id, 'message': 'Fichier reçu avec succès'}), 201

    except Exception as e:
        app.logger.error(f"Erreur lors de l'upload : {e}")
        return jsonify({'error': str(e)}), 500


def notify_user(file_id, email):
    """
    Exemple de fonction pour envoyer une notification (ou appeler un autre service).
    """
    try:
        # Exemple de notification par email (SMTP simplifié)
        with smtplib.SMTP('localhost') as smtp:
            smtp.sendmail(
                from_addr='no-reply@itransfer.com',
                to_addrs=email,
                msg=f"Votre fichier a été uploadé avec succès. ID: {file_id}"
            )
        app.logger.info(f"Notification envoyée à {email} pour le fichier {file_id}")
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de la notification : {e}")

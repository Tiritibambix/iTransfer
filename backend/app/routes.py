from flask import request, jsonify
from . import app, db
from .models import FileUpload
import uuid
import hashlib
import smtplib

@app.route('/upload', methods=['POST'])
def upload_file():
    # Récupérer le fichier et l'email
    file = request.files['file']
    email = request.form['email']
    
    # Identifier l'upload
    file_id = str(uuid.uuid4())
    
    # Encryptage (exemple simple, à adapter selon vos besoins)
    encrypted_data = hashlib.sha256(file.read()).hexdigest()
    
    # Sauvegarder dans la base de données
    new_file = FileUpload(id=file_id, filename=file.filename, email=email, encrypted_data=encrypted_data)
    db.session.add(new_file)
    db.session.commit()
    
    # Envoi d'un email (structure simplifiée)
    send_email(email, file_id)
    
    return jsonify({'file_id': file_id})

def send_email(recipient, file_id):
    with smtplib.SMTP('localhost') as smtp:
        # Logique pour envoyer un email au destinataire
        pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Initialisation de Flask
app = Flask(__name__)
CORS(app)

# Configuration des uploads
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuration SMTP
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_EMAIL = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Configuration de la base de données
DATABASE_URL = "postgresql://your_username:your_password@db:5432/uploads_db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Modèle de données pour les fichiers uploadés
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")  # "uploaded", "email_sent"
    upload_time = Column(DateTime, default=datetime.utcnow)

# Créer les tables si elles n'existent pas
Base.metadata.create_all(engine)

# Route pour l'upload des fichiers
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'email' not in request.form:
        return jsonify({'error': 'No file or email provided'}), 400

    file = request.files['file']
    recipient_email = request.form['email']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Enregistrer les informations dans la base de données
    uploaded_file = UploadedFile(filename=filename, filepath=filepath, email=recipient_email, status="uploaded")
    session.add(uploaded_file)
    session.commit()

    # Envoi de l'email
    email_status = send_email(recipient_email, filename, filepath)
    if email_status:
        # Mettre à jour le statut dans la base de données
        uploaded_file.status = "email_sent"
        session.commit()
        return jsonify({'message': 'File uploaded and email sent successfully'}), 200
    else:
        return jsonify({'error': 'File uploaded but email could not be sent'}), 500

# Fonction pour envoyer un email via SMTP
def send_email(to_email, filename, filepath):
    try:
        # Création du message
        message = MIMEMultipart()
        message['From'] = SMTP_EMAIL
        message['To'] = to_email
        message['Subject'] = "Fichier téléchargé avec succès"

        body = f"""
        Bonjour,

        Le fichier "{filename}" a été téléchargé avec succès. Vous pouvez le récupérer en suivant le lien ci-dessous :
        http://localhost:5000/uploads/{filename}

        Cordialement,
        Votre Service d'Upload.
        """
        message.attach(MIMEText(body, 'plain'))

        # Connexion au serveur SMTP et envoi
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, message.as_string())

        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        return False

# Route pour servir les fichiers uploadés
@app.route('/uploads/<filename>', methods=['GET'])
def get_uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# Route pour obtenir les informations des fichiers uploadés
@app.route('/uploads', methods=['GET'])
def get_uploads():
    files = session.query(UploadedFile).all()
    return jsonify([
        {
            "id": file.id,
            "filename": file.filename,
            "filepath": file.filepath,
            "email": file.email,
            "status": file.status,
            "upload_time": file.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        for file in files
    ])

if __name__ == "__main__":
    app.run(debug=True)

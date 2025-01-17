from . import db

class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(256), nullable=False)
    sender_email = db.Column(db.String(255), nullable=False)
    encrypted_data = db.Column(db.String(256), nullable=False)
    uploaded_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    downloaded = db.Column(db.Boolean, default=False)
    files_summary = db.Column(db.Text)  # Pour stocker le résumé des fichiers
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

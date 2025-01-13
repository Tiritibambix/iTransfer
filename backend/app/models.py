from .database import db

class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False)  # L'email est requis
    encrypted_data = db.Column(db.String(256), nullable=False)  # Hash du fichier
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

from . import db
import json

class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False)
    sender_email = db.Column(db.String(256), nullable=False)
    encrypted_data = db.Column(db.String(256), nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    files_list = db.Column(db.Text, nullable=True)  # Stocke la liste des fichiers en JSON

    def set_files_list(self, files):
        """Convertit et stocke la liste des fichiers en JSON"""
        self.files_list = json.dumps(files) if files else None

    def get_files_list(self):
        """Récupère et désérialise la liste des fichiers"""
        return json.loads(self.files_list) if self.files_list else []

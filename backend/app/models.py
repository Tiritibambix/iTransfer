from datetime import datetime
from .app import db

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<FileUpload {self.filename}>'

from . import db

class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    recipient_email = db.Column(db.String(256), nullable=False)
    sender_email = db.Column(db.String(256), nullable=False)
    encrypted_data = db.Column(db.String(256), nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

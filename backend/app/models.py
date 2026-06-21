import json

from . import db


class FileUpload(db.Model):
    __tablename__ = 'file_upload'

    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False)
    sender_email = db.Column(db.String(256), nullable=False)
    # Historical name kept for schema compatibility. Holds a SHA-256 hex
    # digest of the stored file, used for integrity checks only.
    encrypted_data = db.Column(db.String(256), nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    files_list = db.Column(db.Text, nullable=True)

    # Outcome of each background notification attempt: NULL (never attempted),
    # 'pending', 'sent', or 'failed'. Populated by the background email
    # executor in routes.py; see _ensure_notification_columns() in __init__.py
    # for how these columns reach already-deployed databases.
    notification_status_recipient = db.Column(db.String(16), nullable=True)
    notification_error_recipient = db.Column(db.String(500), nullable=True)
    notification_status_sender = db.Column(db.String(16), nullable=True)
    notification_error_sender = db.Column(db.String(500), nullable=True)
    notification_status_download = db.Column(db.String(16), nullable=True)
    notification_error_download = db.Column(db.String(500), nullable=True)

    def set_files_list(self, files):
        self.files_list = json.dumps(files) if files else None

    def get_files_list(self):
        return json.loads(self.files_list) if self.files_list else []

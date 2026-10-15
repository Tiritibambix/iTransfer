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

    # Optional free-text message from the sender to the recipient, shown in the
    # recipient email and on the download page. VARCHAR (not TEXT) so the
    # startup migration can add it with DEFAULT NULL on MySQL/MariaDB.
    message = db.Column(db.String(2000), nullable=True)
    # The sender's UI language at the time of the transfer, used for every
    # email tied to it (recipient notification, sender confirmation, and the
    # later download alert). Stored because the download notification fires
    # much later, at download time, when there is no request to read it from.
    language = db.Column(db.String(8), nullable=True)

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

    # Human-readable public link (e.g. "quiet-river-still-dawn"), generated at
    # upload time. The id (uuid) above stays the real primary key and the temp
    # directory name; slug only ever appears in URLs. Nullable so rows created
    # before this column existed keep resolving by id (see the fallback
    # lookup in routes.py).
    slug = db.Column(db.String(64), nullable=True)

    # Optional password gate on the transfer. Holds a werkzeug password hash,
    # never the plaintext value.
    password_hash = db.Column(db.String(255), nullable=True)

    # Optional cap on successful downloads, on top of the existing time-based
    # expiry. NULL means unlimited (the historical default). download_count
    # is nullable rather than NOT NULL DEFAULT 0 so it fits the same additive
    # migration path as every other column here; treat a NULL as 0 when read.
    download_limit = db.Column(db.Integer, nullable=True)
    download_count = db.Column(db.Integer, nullable=True)

    def set_files_list(self, files):
        self.files_list = json.dumps(files) if files else None

    def get_files_list(self):
        return json.loads(self.files_list) if self.files_list else []

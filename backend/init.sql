CREATE TABLE IF NOT EXISTS file_upload (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    sender_email VARCHAR(256) NOT NULL,
    encrypted_data VARCHAR(256) NOT NULL,
    downloaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    files_list TEXT, -- Stocke la liste des fichiers en JSON
    notification_status_recipient VARCHAR(16) DEFAULT NULL,
    notification_error_recipient VARCHAR(500) DEFAULT NULL,
    notification_status_sender VARCHAR(16) DEFAULT NULL,
    notification_error_sender VARCHAR(500) DEFAULT NULL,
    notification_status_download VARCHAR(16) DEFAULT NULL,
    notification_error_download VARCHAR(500) DEFAULT NULL
);

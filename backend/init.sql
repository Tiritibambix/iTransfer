CREATE TABLE IF NOT EXISTS file_uploads (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    encrypted_data VARCHAR(256) NOT NULL,
    is_archive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS archive_contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_upload_id VARCHAR(36),
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT,
    FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id)
);

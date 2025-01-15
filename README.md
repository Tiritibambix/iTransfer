# iTransfer - Secure File Transfer System

iTransfer is a secure file transfer system that allows users to share files and receive email notifications when files are uploaded and downloaded.

## Features

- 🚀 Easy file upload and download
- 📧 Email notifications for both sender and recipient
- 🔒 Secure file storage
- 💼 Professional email templates
- ⚙️ Configurable SMTP settings
- 🌐 Support for reverse proxy deployment
- 🔐 HTTPS enforcement in production
- 🔌 Flexible port configuration

## Email Notifications

The system sends three types of email notifications:
1. To the recipient when a file is uploaded
2. To the sender when their file is uploaded
3. To the sender when their file is downloaded

All emails are sent using a professional HTML template with both HTML and plain text versions for maximum compatibility.

### Email Delivery Features

- Support for multiple SMTP configurations:
  - Gmail (ports 587 and 465)
  - Office 365 (port 587)
  - OVH (port 465)
  - Custom SMTP servers
- Automatic protocol selection (STARTTLS or SSL)
- Enhanced email headers for better deliverability
- Professional HTML templates
- Multipart emails (HTML + plain text)
- Anti-spam measures

## Installation

### Prerequisites

- Docker
- Docker Compose
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/iTransfer.git
cd iTransfer
```

2. Set up the database initialization file:
   - Either download [init.sql](https://github.com/yourusername/iTransfer/blob/main/backend/init.sql) and place it in `backend/init.sql`
   - Or create the file manually at `backend/init.sql` with the following content:
```sql
CREATE TABLE IF NOT EXISTS file_upload (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    sender_email VARCHAR(256) NOT NULL,
    encrypted_data VARCHAR(256) NOT NULL,
    downloaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

3. Create your `docker-compose.yml` for local development:

```yaml
# Docker Compose configuration for iTransfer - Development Environment
version: '3.8'

services:
  # Frontend service: React application
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 3500)
      # - container_port: Must remain 80 (React default port)
      - "3500:80"
    depends_on:
      - backend
    networks:
      - itransfer-network
    environment:
      # Backend URL must match the host_port defined in backend service
      - REACT_APP_API_URL=http://localhost:5500
    volumes:
      - ./frontend:/app
      - /app/node_modules

  # Backend service: Flask application
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 5500)
      # - container_port: Must remain 5000 (Flask default port)
      - "5500:5000"
    depends_on:
      - db
    networks:
      - itransfer-network
    environment:
      # Database configuration
      - DATABASE_URL=mysql+mysqldb://itransfer:password@db/itransfer
      
      # SMTP configuration
      - SMTP_CONFIG_PATH=/app/data/smtp_config.json
      
      # Security settings (change these!)
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=password
      
      # URLs must match the ports defined above
      - FRONTEND_URL=http://localhost:3500
      - BACKEND_URL=http://localhost:5500
      
      # Development settings
      - FLASK_ENV=development
      - FORCE_HTTPS=false
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
      - data:/app/data

  # Database service: MySQL
  db:
    image: mysql:8.0
    command: --default-authentication-plugin=mysql_native_password
    restart: always
    networks:
      - itransfer-network
    environment:
      - MYSQL_DATABASE=itransfer
      - MYSQL_USER=itransfer
      - MYSQL_PASSWORD=password
      - MYSQL_ROOT_PASSWORD=root
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql

networks:
  itransfer-network:
    driver: bridge

volumes:
  mysql_data:
  uploads:
  data:
```

4. Start the application:
```bash
docker-compose up -d
```

5. Access the application:
- Frontend: http://localhost:[your_frontend_port] (default: 3500)
- Backend API: http://localhost:[your_backend_port] (default: 5500)

### Production Deployment

For production deployment behind a reverse proxy, use this `docker-compose.yml`:

```yaml
# Docker Compose configuration for iTransfer - Production Environment
version: '3.8'

services:
  # Frontend service: React application
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3500:80"
    depends_on:
      - backend
    networks:
      - itransfer-network
    environment:
      # Production backend URL (with HTTPS)
      - REACT_APP_API_URL=https://api.yourdomain.com
    volumes:
      - ./frontend:/app
      - /app/node_modules

  # Backend service: Flask application
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5500:5000"
    depends_on:
      - db
    networks:
      - itransfer-network
    environment:
      # Database configuration (use strong passwords)
      - DATABASE_URL=mysql+mysqldb://itransfer:strong_password@db/itransfer
      
      # SMTP configuration
      - SMTP_CONFIG_PATH=/app/data/smtp_config.json
      
      # Security settings (use strong credentials)
      - ADMIN_USERNAME=secure_admin_username
      - ADMIN_PASSWORD=secure_admin_password
      
      # Production URLs (with HTTPS)
      - FRONTEND_URL=https://yourdomain.com
      - BACKEND_URL=https://api.yourdomain.com
      
      # Production settings
      - FLASK_ENV=production
      - FORCE_HTTPS=true
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
      - data:/app/data

  # Database service: MySQL
  db:
    image: mysql:8.0
    command: --default-authentication-plugin=mysql_native_password
    restart: always
    networks:
      - itransfer-network
    environment:
      - MYSQL_DATABASE=itransfer
      - MYSQL_USER=itransfer
      - MYSQL_PASSWORD=strong_password
      - MYSQL_ROOT_PASSWORD=strong_root_password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql

networks:
  itransfer-network:
    driver: bridge

volumes:
  mysql_data:
  uploads:
  data:
```

Configure your reverse proxy (example for Nginx):
```nginx
# Frontend
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Backend
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Start the application:
```bash
docker-compose up -d
```

## Development

### Project Structure

```
iTransfer/
├── frontend/          # React frontend application
├── backend/           # Flask backend application
│   ├── app/          # Application code
│   ├── uploads/      # Uploaded files
│   ├── data/         # Configuration files
│   └── init.sql      # Database initialization script
└── docker-compose.yml # Docker configuration
```

### Local Development

1. Start the services:
```bash
docker-compose up -d
```

2. Watch logs:
```bash
docker-compose logs -f
```

### Troubleshooting

#### Database Issues

If you encounter database-related issues:

1. Verify that `backend/init.sql` exists and contains the correct table definition:
```sql
CREATE TABLE IF NOT EXISTS file_upload (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    sender_email VARCHAR(256) NOT NULL,
    encrypted_data VARCHAR(256) NOT NULL,
    downloaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. If the file is missing or incorrect:
   - Stop the containers: `docker-compose down`
   - Create or fix the `init.sql` file
   - Remove the database volume: `docker-compose down -v`
   - Start the containers again: `docker-compose up -d`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
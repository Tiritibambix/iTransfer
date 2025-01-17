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
- 📁 Smart file handling (ZIP for multiple files, direct download for single files)
- 📝 Detailed file listings in all notifications

## Email Notifications

The system sends three types of email notifications:
1. To the recipient when a file is uploaded (includes detailed file list)
2. To the sender when their file is uploaded (includes detailed file list)
3. To the sender when their file is downloaded (includes detailed file list)

All notifications include:
- Complete list of transferred files with sizes
- Total transfer size
- Download link (when applicable)
- Professional HTML template with both HTML and plain text versions

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

### File Handling Features

- Smart compression:
  - Multiple files are automatically compressed into a ZIP
  - Single files are transferred directly without compression
- Folder structure preservation in ZIP files
- Human-readable file sizes (KB, MB, GB)
- Detailed file listings in all notifications

## Installation

### Prerequisites

- Docker
- Docker Compose
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/tiritibambix/iTransfer.git
cd iTransfer
```

2. Set up the database initialization file:
   - Either download [init.sql](https://github.com/tiritibambix/iTransfer/blob/main/backend/init.sql) and place it in `backend/init.sql`
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
services:
  frontend:
    image: tiritibambix/itransfer-frontend
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 3500)
      # - container_port: Must remain 80 (React default port)
      - "3500:80"
    environment:
      - BACKEND_URL=http://localhost:5500  # Change 5500 if you modified backend port
    depends_on:
      - backend
    networks:
      - itransfer-network

  backend:
    image: tiritibambix/itransfer-backend
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 5500)
      # - container_port: Must remain 5000 (Flask default port)
      - "5500:5000"
    environment:
      - FRONTEND_URL=http://localhost:3500  # Change 3500 if you modified frontend port
      - ADMIN_USERNAME=admin  # Change these credentials
      - ADMIN_PASSWORD=admin  # Change these credentials
      - DATABASE_URL=mysql+mysqldb://mariadb_user:mariadb_pass@db/mariadb_db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(openssl rand -base64 32)}  # Secret key for JWT tokens
    volumes:
      - ./backend/data:/app/data
      - ./backend/uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
    networks:
      - itransfer-network

  db:
    image: mariadb
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: mariadb_db
      MYSQL_USER: mariadb_user
      MYSQL_PASSWORD: mariadb_pass
    ports:
      - "3306:3306"
    volumes:
      - ./db_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -u root --password=$MYSQL_ROOT_PASSWORD || echo 'Healthcheck failed' >> /var/log/healthcheck.log"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - itransfer-network

networks:
  itransfer-network:
    driver: bridge
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

1. Set up the database initialization file:
   - Either download [init.sql](https://github.com/tiritibambix/iTransfer/blob/main/backend/init.sql) and place it in `backend/init.sql`
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

2. Create your `docker-compose.yml` for production development:

```yaml
services:
  frontend:
    image: tiritibambix/itransfer-frontend
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 3500)
      # - container_port: Must remain 80 (React default port)
      - "3500:80"
    environment:
      # Public backend URL (with https:// if behind reverse proxy)
      # Proxy example: https://api.itransfer.domain.tld
      - BACKEND_URL=https://api.itransfer.domain.tld
    depends_on:
      - backend
    networks:
      - itransfer-network

  backend:
    image: tiritibambix/itransfer-backend
    ports:
      # Port mapping format: "host_port:container_port"
      # - host_port: Can be changed to any available port on your system (default: 5500)
      # - container_port: Must remain 5000 (Flask default port)
      - "5500:5000"
    environment:
      # Public frontend URL (with https:// if behind reverse proxy)
      # Proxy example: https://itransfer.domain.tld
      - FRONTEND_URL=https://itransfer.domain.tld
      - ADMIN_USERNAME=admin  # Change these credentials
      - ADMIN_PASSWORD=admin  # Change these credentials
      - DATABASE_URL=mysql+mysqldb://mariadb_user:mariadb_pass@db/mariadb_db
      - FORCE_HTTPS=true
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(openssl rand -base64 32)}  # Secret key for JWT tokens
    volumes:
      - ./backend/data:/app/data
      - ./backend/uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
    networks:
      - itransfer-network

  db:
    image: mariadb
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: mariadb_db
      MYSQL_USER: mariadb_user
      MYSQL_PASSWORD: mariadb_pass
    ports:
      - "3306:3306"
    volumes:
      - ./db_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -u root --password=$MYSQL_ROOT_PASSWORD || echo 'Healthcheck failed' >> /var/log/healthcheck.log"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - itransfer-network

networks:
  itransfer-network:
    driver: bridge
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
├── LICENSE                 # Project license file
├── README.md              # Project documentation
├── backend/               # Flask backend application
│   ├── Dockerfile        # Backend container configuration
│   ├── app/              # Application package
│   │   ├── __init__.py  # Package initialization
│   │   ├── app.py       # Flask application setup
│   │   ├── config.py    # Application configuration
│   │   ├── models.py    # Database models
│   │   ├── routes.py    # API endpoints
│   ├── entrypoint.sh    # Container entry point script
│   ├── init.sql         # Database initialization script
│   ├── run.py           # Application entry point
├── docker-compose.yml    # Docker services configuration
├── frontend/            # React frontend application
│   ├── Dockerfile      # Frontend container configuration
│   ├── package.json    # Node.js dependencies
│   ├── public/         # Static files
│   │   ├── index.html # Main HTML file
│   ├── src/           # Source files
│   │   ├── App.js           # Main React component
│   │   ├── Login.js         # Authentication component
│   │   ├── PrivateRoute.js  # Route protection component
│   │   ├── SMTPSettings.js  # Email settings component
│   │   ├── index.css        # Global styles
│   │   ├── index.js         # React entry point
└── requirements.txt     # Python dependencies
```

The project follows a typical client-server architecture:

- **Backend**: A Flask application that handles:
  - File upload and storage
  - Email notifications
  - Database operations
  - Authentication

- **Frontend**: A React application providing:
  - User interface for file uploads
  - Admin dashboard
  - SMTP configuration interface
  - Protected routes

Both applications are containerized using Docker for easy deployment and consistent environments.

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

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
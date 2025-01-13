# iTransfer

[![Build and Push Docker Images](https://github.com/tiritibambix/iTransfer/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/tiritibambix/iTransfer_1minAI/actions/workflows/docker-build-push.yml)

A file transfer application with web interface, secure backend, and email notifications.

## Features

- Responsive user interface
- File upload with progress bar
- Automatic email notifications
- Secure admin interface
- REST API backend
- Easy deployment with Docker
- File management with MariaDB database

## Prerequisites

- Docker
- Docker Compose
- Access to ports 3500 (frontend), 5500 (backend), and 3306 (MariaDB)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/tiritibambix/iTransfer.git
cd iTransfer
```

2. Create necessary directories:
```bash
mkdir -p backend/data backend/uploads
```

3. Start the containers:
```bash
docker-compose up -d
```

4. Access the web interface at http://localhost:3500

## Detailed Installation Guide

### 1. System Requirements

- Docker Engine 20.10.0 or later
- Docker Compose 2.0.0 or later
- At least 1GB of free RAM
- At least 1GB of free disk space

### 2. Installation Steps

1. **Clone the Repository**
```bash
git clone https://github.com/tiritibambix/iTransfer.git
cd iTransfer
```

2. **Create Required Directories**
```bash
mkdir -p backend/data backend/uploads
chmod -R 777 backend/data backend/uploads
```

3. **Configure Environment**

Edit `docker-compose.yml` to set your environment variables:
```yaml
# Backend service environment variables
FRONTEND_URL: "http://localhost:3500"  # Change if using different host/port
ADMIN_USERNAME: "adminuser"            # Change this
ADMIN_PASSWORD: "adminuserpassword"    # Change this
DATABASE_URL: "mysql://mariadb_user:mariadb_pass@db/mariadb_db"

# Database service environment variables
MYSQL_ROOT_PASSWORD: "rootpassword"    # Change this
MYSQL_DATABASE: "mariadb_db"
MYSQL_USER: "mariadb_user"            # Change this
MYSQL_PASSWORD: "mariadb_pass"         # Change this
```

4. **Start the Services**
```bash
# Build the images
docker-compose build

# Start the services
docker-compose up -d
```

5. **Verify Installation**
```bash
# Check if all containers are running
docker-compose ps

# Check container logs
docker-compose logs -f
```

### 3. SMTP Configuration

1. Access the admin interface at http://localhost:3500/admin
2. Log in with your configured admin credentials
3. Go to SMTP Settings and configure:
   - SMTP Server (e.g., smtp.gmail.com)
   - SMTP Port (e.g., 465 for SSL)
   - SMTP Username
   - SMTP Password
   - Sender Email Address

### 4. Testing the Installation

1. **Test File Upload**
   - Go to http://localhost:3500
   - Upload a file and enter a recipient email
   - Verify that the file uploads successfully
   - Check that the recipient receives the email

2. **Test Admin Interface**
   - Go to http://localhost:3500/admin
   - Log in with admin credentials
   - Verify access to all admin features

## Usage Guide

### File Upload
1. Visit http://localhost:3500
2. Drag and drop files or click to select
3. Enter recipient's email address
4. Click "Send"
5. Recipient will receive an email with download link

### Admin Tasks
1. Access admin interface at http://localhost:3500/admin
2. Configure SMTP settings
3. Monitor file uploads
4. Manage system settings

## Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose build

# Restart specific service
docker-compose restart [service_name]

# View service status
docker-compose ps
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check logs: `docker-compose logs [service_name]`
   - Verify port availability
   - Check directory permissions

2. **Email notifications not working**
   - Verify SMTP settings
   - Check admin interface logs
   - Ensure correct email format

3. **Upload fails**
   - Check backend logs
   - Verify directory permissions
   - Check disk space

### Logs Location

- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`
- Database logs: `docker-compose logs db`

## Security Considerations

1. **Change Default Credentials**
   - Admin username/password
   - Database passwords
   - SMTP credentials

2. **File Security**
   - Files are stored in `backend/uploads`
   - Download links expire after 7 days
   - Files are encrypted at rest

## Maintenance

### Backup

1. **Database Backup**
```bash
docker-compose exec db mysqldump -u root -p mariadb_db > backup.sql
```

2. **File Backup**
```bash
tar -czf uploads_backup.tar.gz backend/uploads
```

### Updates

1. **Update Application**
```bash
git pull
docker-compose build
docker-compose up -d
```

## Support

- GitHub Issues: [Report a bug](https://github.com/tiritibambix/iTransfer/issues)
- Documentation: [Wiki](https://github.com/tiritibambix/iTransfer/wiki)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
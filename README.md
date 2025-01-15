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

2. Create a .env file (optional):
```bash
# Database
DB_PASSWORD=your_db_password
DB_ROOT_PASSWORD=your_root_password

# Admin access
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password

# Deployment
BACKEND_URL=https://api.yourdomain.com  # If behind reverse proxy
FRONTEND_URL=https://yourdomain.com     # If behind reverse proxy
FORCE_HTTPS=true                        # Force HTTPS in production
PROXY_COUNT=1                           # Number of reverse proxies
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3500
- Backend API: http://localhost:5500

### SMTP Configuration

1. Log in to the admin interface at http://localhost:3500/admin
2. Configure your SMTP settings:
   - SMTP Server (e.g., smtp.gmail.com)
   - SMTP Port (587 for STARTTLS, 465 for SSL)
   - SMTP Username
   - SMTP Password
   - Sender Email

The application will automatically detect the correct protocol based on the port:
- Port 465: Uses SSL
- Port 587 (or others): Uses STARTTLS

### Production Deployment

For production deployment behind a reverse proxy:

1. Set environment variables in .env:
```bash
BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
FORCE_HTTPS=true
PROXY_COUNT=1  # Adjust based on your setup
```

2. Configure your reverse proxy (example for Nginx):
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

3. Start the application:
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
│   └── data/         # Configuration files
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

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
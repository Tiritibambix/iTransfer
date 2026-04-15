<p align="center">
  <img src="https://raw.githubusercontent.com/tiritibambix/iTransfer/main/frontend/src/assets/banner.png" width="400" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-amd64%20%7C%20arm64-blue" alt="Platform Support" />
  <img src="https://img.shields.io/badge/License-GPL--3.0-purple" alt="License" />
  <img src="https://img.shields.io/badge/Stack-Flask%20%2B%20React%20%2B%20MariaDB-darkviolet" alt="Stack" />
</p>

# iTransfer

Self-hosted file transfer system. Upload files, share a download link, get notified by email when the recipient downloads. No cloud, no third party.

## ⚠️ Security Notice

This application has been coded with the help of AI and is provided as-is. While reasonable security measures have been implemented (see the Security section below), no independent audit has been performed. You are responsible for reviewing the code, assessing the risks for your use case, and validating that the deployment meets your security requirements before exposing this to the internet. The repository owner accepts no liability for any damages or data loss resulting from the use of this software.

## Features

- Upload files or folders via drag & drop
- Automatic ZIP packaging for multiple files, direct download for single files
- Configurable link expiration: 3, 5, 7 or 10 days
- Email notifications: recipient on upload, sender on upload and on download
- Admin panel: list and delete transfers, configure SMTP
- JWT authentication on protected routes
- Rate limiting on login and upload endpoints
- Server-side email validation
- Automatic cleanup of expired files and database records
- HTTPS enforcement and reverse proxy support
- Multi-arch Docker images: `amd64` / `arm64`

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python / Flask + Gunicorn |
| Database | MariaDB |
| Containerization | Docker + Docker Compose |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── __init__.py      # App factory, scheduler, CORS
│   │   ├── auth.py          # JWT helpers
│   │   ├── config.py        # Configuration
│   │   ├── models.py        # Database models
│   │   ├── paths.py         # Path sanitization (CodeQL sanitizer)
│   │   └── routes.py        # API endpoints
│   ├── Dockerfile
│   ├── init.sql
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── Admin.jsx        # Admin panel (transfers + SMTP)
│   │   ├── App.jsx          # Upload interface
│   │   ├── Download.jsx     # Download page
│   │   ├── Login.jsx        # Authentication
│   │   ├── PrivateRoute.jsx # Route guard
│   │   ├── main.jsx         # Entry point
│   │   └── index.css        # Design system
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── requirements.txt
```

## Installation

### Prerequisites

- Docker
- Docker Compose

### Quick Start (local)

```bash
git clone https://github.com/tiritibambix/iTransfer.git
cd iTransfer
```

Create a `docker-compose.yml`:

```yaml
services:
  frontend:
    image: tiritibambix/itransfer-frontend
    ports:
      - "3500:80"
    environment:
      - BACKEND_URL=http://localhost:5500
    depends_on:
      - backend
    networks:
      - itransfer-network

  backend:
    image: tiritibambix/itransfer-backend
    ports:
      - "5500:5000"
    environment:
      - FRONTEND_URL=http://localhost:3500
      - ADMIN_USERNAME=admin          # Change this
      - ADMIN_PASSWORD=admin          # Change this
      - DATABASE_URL=mysql+mysqldb://mariadb_user:mariadb_pass@db/mariadb_db
      - TIMEZONE=Europe/Paris
      - JWT_SECRET_KEY=changeme       # Change this
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
    volumes:
      - ./db_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -u root --password=$MYSQL_ROOT_PASSWORD"]
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

```bash
docker compose up -d
```

Access the app at `http://localhost:3500`.

### Production (behind reverse proxy)

Replace the environment variables with your public URLs:

```yaml
environment:
  - BACKEND_URL=https://api.itransfer.yourdomain.tld   # frontend service
  - FRONTEND_URL=https://itransfer.yourdomain.tld      # backend service
  - FORCE_HTTPS=true
```

Nginx example:

```nginx
# Frontend
server {
    listen 443 ssl;
    server_name itransfer.yourdomain.tld;
    location / {
        proxy_pass http://localhost:3500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Backend
server {
    listen 443 ssl;
    server_name api.itransfer.yourdomain.tld;
    location / {
        proxy_pass http://localhost:5500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SMTP Configuration

Configure SMTP from the admin panel (`/admin` → SMTP tab) or directly via environment variables. The backend supports any SMTP server with SSL (port 465) or STARTTLS (port 587).

Tested with OVH, Gmail, Office 365 and generic SMTP.

For reliable delivery to Gmail/Yahoo, your domain needs SPF, DKIM and DMARC records. Without them, messages will be rejected.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FRONTEND_URL` | yes | `http://localhost:3500` | Public frontend URL |
| `BACKEND_URL` | yes | `http://localhost:5500` | Public backend URL |
| `ADMIN_USERNAME` | yes | — | Admin login |
| `ADMIN_PASSWORD` | yes | — | Admin password |
| `DATABASE_URL` | yes | SQLite fallback | MariaDB connection string |
| `JWT_SECRET_KEY` | yes | random | JWT signing key — set a stable value |
| `TIMEZONE` | no | `Europe/Paris` | Timezone for expiry display |
| `FORCE_HTTPS` | no | `true` | Enforce HTTPS in generated URLs |
| `PROXY_COUNT` | no | `1` | Number of reverse proxies in front |

## Troubleshooting

**Files not received / emails rejected**
Check SPF, DKIM and DMARC records on your sending domain. Most major providers (Gmail, Yahoo) reject unauthenticated mail since early 2024.

**Database not initializing**
Make sure `backend/init.sql` exists before the first `docker compose up`. If the DB volume already exists without the table, run:
```bash
docker compose down -v
docker compose up -d
```

**Logs**
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## License

GPL-3.0 — see [LICENSE](LICENSE).
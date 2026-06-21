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

This application has been coded with the help of AI and is provided as-is. While reasonable security measures have been implemented, no independent audit has been performed. You are responsible for reviewing the code, assessing the risks for your use case, and validating that the deployment meets your security requirements before exposing this to the internet. The repository owner accepts no liability for any damages or data loss resulting from the use of this software.

## Features

- Upload files or folders via drag & drop
- Automatic ZIP packaging for multiple files, direct download for single files
- Configurable link expiration: 3, 5, 7 or 10 days
- Email notifications: recipient on upload, sender on upload and on download — sent in the background with automatic retry on transient SMTP failures
- Admin panel: list and delete transfers (with per-notification delivery status), configure SMTP, DNS-based deliverability checker (SPF/DMARC/DKIM)
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
│   │   ├── deliverability.py # SPF/DMARC/DKIM DNS checks
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

Configure SMTP from the admin panel (`/admin` → SMTP tab). The backend supports any SMTP server with SSL (port 465) or STARTTLS (port 587).

Tested with OVH, Gmail, Office 365 and generic SMTP.

### Domain authentication (SPF, DKIM, DMARC)

Gmail and Yahoo reject or spam-folder unauthenticated mail since February 2024. iTransfer relays through *your own* SMTP account — it never sends mail directly — so the records below must exist on the domain of the **sender email** configured in the SMTP tab (the part after the `@`), not on iTransfer's own infrastructure.

**SPF** authorizes your SMTP provider to send mail "as" your domain. Add one TXT record at your domain's apex (`@`):

```
v=spf1 include:<your-provider's-SPF-include> ~all
```

| Provider | SPF include |
|---|---|
| OVH | `include:mx.ovh.com` |
| Gmail / Google Workspace | `include:_spf.google.com` |
| Office 365 | `include:spf.protection.outlook.com` |

If more than one service sends mail "as" your domain (iTransfer, your regular mailbox, a marketing tool, etc.), combine them into a **single** SPF record with multiple `include:` mechanisms — never publish two separate `v=spf1` TXT records, this silently breaks SPF entirely (RFC 7208 treats it as a hard PermError). The admin panel's deliverability checker (below) explicitly detects and flags this.

**DMARC** tells receivers what to do when SPF/DKIM fail. Add one TXT record at `_dmarc.yourdomain.tld`:

```
v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@yourdomain.tld
```

- `p=none` — monitoring only, offers no actual protection (a stale leftover from initial DMARC rollout is common — check this hasn't stayed at `none` for years).
- `p=quarantine` — failing mail goes to spam. Recommended starting point.
- `p=reject` — failing mail is rejected outright. Strongest, move here once `quarantine` hasn't caused issues with legitimate mail.

**DKIM** cryptographically signs outgoing mail. DKIM is configured and signed by *your SMTP provider*, not by iTransfer — iTransfer only relays through your authenticated SMTP account, it does not sign messages itself. Enable it and find your selector in your provider's control panel:

| Provider | Where to enable DKIM |
|---|---|
| OVH | Web Cloud panel → Emails → DKIM (per-domain toggle) |
| Gmail / Google Workspace | Admin console → Apps → Google Workspace → Gmail → Authenticate email |
| Office 365 | Microsoft 365 Defender → Policies & rules → Email authentication settings → DKIM |

### Re-verify, don't rely on memory

DNS records drift: a registrar UI change can silently overwrite a TXT record, another service added later can introduce a second conflicting SPF record, or a DMARC policy set to `p=none` years ago may never have been tightened. "I checked this a while ago" is not the same as "this is correct right now." Use the **Check deliverability** button in the admin SMTP tab to re-run live SPF/DMARC/(optional DKIM) DNS lookups any time mail seems to be landing in spam — especially after any DNS or registrar change, and periodically even if nothing else changed.

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

## Upgrading

Newer versions may add columns to the database schema automatically on startup (additive only — existing data is never dropped or rewritten). As with any schema change, back up `./db_data` before pulling a new image version.

## Troubleshooting

**Files not received / emails rejected, or landing in spam**

1. Open the admin panel → SMTP tab → **Check deliverability**. This runs live DNS lookups against your sender domain for SPF and DMARC (and DKIM if you supply your provider's selector), and explicitly calls out a missing record, a misconfigured DMARC policy, or the "multiple SPF records" mistake.
2. If the checker reports a problem, see [Domain authentication](#domain-authentication-spf-dkim-dmarc) above for exact record syntax per provider.
3. Re-run the checker after any DNS/registrar change — don't assume a past check is still valid; records can be overwritten by a registrar UI change or by another service adding a conflicting record.
4. Check the admin "Transfers" tab: each transfer shows per-notification send status (recipient / sender / download alert) with the last SMTP error on hover, so you can tell whether an email was actually attempted and what failed.

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

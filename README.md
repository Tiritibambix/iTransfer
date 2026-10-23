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

<p align="center">
  <img src="docs/screenshots/send.jpg" width="48%" alt="Send page" />
  <img src="docs/screenshots/download.jpg" width="48%" alt="Download page" />
</p>

## ⚠️ Security Notice

This application has been coded with the help of AI and is provided as-is. While reasonable security measures have been implemented, no independent audit has been performed. You are responsible for reviewing the code, assessing the risks for your use case, and validating that the deployment meets your security requirements before exposing this to the internet. The repository owner accepts no liability for any damages or data loss resulting from the use of this software.

## Features

- Upload files or folders via drag & drop
- Resumable uploads (tus protocol): a dropped connection or closed laptop lid resumes from where it left off instead of restarting multi-GB transfers from zero
- Automatic ZIP packaging for multiple files, direct download for single files
- Streamed uploads and downloads with chunked hashing, suitable for multi-GB transfers
- Human-readable transfer links (e.g. `quiet-river-still-dawn`) instead of a raw ID
- Optional password protection and optional download-count limit per transfer
- Configurable link expiration: 3, 5, 7 or 10 days
- Full-bleed rotating background with a frosted-glass card, photos bundled locally (no third-party image service)
- Email notifications: recipient on upload, sender on upload and on download, sent in the background with automatic retry on transient SMTP failures
- Multilingual interface and emails (English, Français, Español, Deutsch, Italiano): one language, auto-detected from the browser with a manual switcher, applies to the whole UI and to every email sent from that session
- Optional personal message to the recipient, shown in the notification email and on the download page
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
│   │   ├── __init__.py      # App init, schema migration, scheduler, CORS, email executor
│   │   ├── auth.py          # JWT helpers
│   │   ├── config.py        # Configuration
│   │   ├── deliverability.py # SPF/DMARC/DKIM DNS checks
│   │   ├── email_i18n.py    # Email translations (EN/FR/ES/DE/IT)
│   │   ├── models.py        # Database models
│   │   ├── paths.py         # Path sanitization (CodeQL sanitizer)
│   │   ├── routes.py        # API endpoints (incl. tus hooks + finalize)
│   │   └── slug.py          # Human-readable transfer link generation
│   ├── Dockerfile
│   ├── init.sql
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── i18n/            # UI translations (index + per-language JSON)
│   │   ├── Admin.jsx        # Admin panel (transfers + SMTP)
│   │   ├── App.jsx          # Upload interface
│   │   ├── Download.jsx     # Download page
│   │   ├── Login.jsx        # Authentication
│   │   ├── LanguageSelector.jsx # Language switcher
│   │   ├── PageBackground.jsx # Rotating full-bleed background + photo credit
│   │   ├── PrivateRoute.jsx # Route guard
│   │   ├── api.js           # authFetch wrapper (handles expired sessions)
│   │   ├── storage.js       # Safe localStorage access
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

  # One-shot init container: the official tusd image runs as a non-root
  # user (uid 1000), but a freshly created volume is owned by root, so tusd
  # fails every upload with "permission denied" until something chowns it.
  # Runs once, exits, then tusd is allowed to start.
  tusd-init:
    image: busybox:latest
    command: ["sh", "-c", "chown -R 1000:1000 /data"]
    volumes:
      - tusd-uploads:/data
    networks:
      - itransfer-network

  # Receives resumable (tus protocol) uploads and notifies the backend once
  # each file is fully received. Not published on the host: the frontend's
  # nginx proxies /files/ to it, and the backend calls it as a webhook, both
  # over itransfer-network.
  tusd:
    image: tusproject/tusd:v2.10.1
    command: >-
      -behind-proxy
      -hooks-http=http://backend:5000/api/tus-hooks?secret=changeme-tus-hook-secret
      -hooks-enabled-events=pre-create,post-finish,post-terminate
      -upload-dir=/data
      -base-path=/files/
    volumes:
      - tusd-uploads:/data
    networks:
      - itransfer-network
    depends_on:
      tusd-init:
        condition: service_completed_successfully
      backend:
        condition: service_started

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
      - TUS_HOOK_SECRET=changeme-tus-hook-secret  # Change this; must match the tusd service above
    volumes:
      - ./backend/data:/app/data
      - ./backend/uploads:/app/uploads
      - tusd-uploads:/data           # Same volume as tusd, so finished files can be moved out of it
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

volumes:
  tusd-uploads:
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

    # Resumable uploads (tus protocol) now flow through this server block too
    # (proxied internally from here to tusd), so it needs the same large-body
    # treatment as the backend block below.
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_read_timeout 1800s;
    proxy_send_timeout 1800s;
    client_body_timeout 1800s;

    location / {
        proxy_pass http://localhost:3500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend
server {
    listen 443 ssl;
    server_name api.itransfer.yourdomain.tld;

    # Required for large uploads. Without these the proxy rejects or cuts
    # multi-GB transfers before they reach the backend (nginx defaults to a
    # 1 MB body limit), which shows up in the browser as "Network error".
    client_max_body_size 0;          # 0 = unlimited, or set e.g. 5000m
    proxy_request_buffering off;     # stream to the backend instead of buffering the whole body first
    proxy_read_timeout 1800s;
    proxy_send_timeout 1800s;
    client_body_timeout 1800s;

    location / {
        proxy_pass http://localhost:5500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Large file uploads

iTransfer is built for big transfers, and uploads use the resumable (tus) protocol: a dropped connection or a closed laptop lid resumes from the last byte the server actually received instead of restarting the file from zero. Two layers in front of the app still impose their own limits you need to raise for multi-GB files.

**Reverse proxy (required).** This is the most common reason a large upload fails with "Network error" while a small file works: nginx caps request bodies at 1 MB by default. Uploads now reach the app through the **frontend** hostname (`/files/`, proxied internally to the `tusd` service), so apply the directives shown in *both* the frontend and backend server blocks above (`client_max_body_size`, the two `proxy_*_timeout` values, `client_body_timeout`, and `proxy_request_buffering off`). On Nginx Proxy Manager, paste them into both proxy hosts' *Advanced* tab. On Traefik there is no body-size limit by default, but raise the responding timeouts.

**Backend (already tuned, optional).** Gunicorn runs threaded workers with a 30 minute request timeout by default, so slow multi-GB downloads are not cut off (uploads no longer pass through Gunicorn at all -- `tusd` receives them directly). Only if a single download can exceed 30 minutes on a slow link do you need to raise `GUNICORN_TIMEOUT` (see [Environment Variables](#environment-variables)).

## SMTP Configuration

Configure SMTP from the admin panel (`/admin` → SMTP tab). The backend supports any SMTP server with SSL (port 465) or STARTTLS (port 587).

Tested with OVH, Gmail, Office 365 and generic SMTP.

### Domain authentication (SPF, DKIM, DMARC)

Gmail and Yahoo reject or spam-folder unauthenticated mail since February 2024. iTransfer relays through *your own* SMTP account and never sends mail directly, so the records below must exist on the domain of the **sender email** configured in the SMTP tab (the part after the `@`), not on iTransfer's own infrastructure.

**SPF** authorizes your SMTP provider to send mail "as" your domain. Add one TXT record at your domain's apex (`@`):

```
v=spf1 include:<your-provider's-SPF-include> ~all
```

| Provider | SPF include |
|---|---|
| OVH | `include:mx.ovh.com` |
| Gmail / Google Workspace | `include:_spf.google.com` |
| Office 365 | `include:spf.protection.outlook.com` |

If more than one service sends mail "as" your domain (iTransfer, your regular mailbox, a marketing tool, etc.), combine them into a **single** SPF record with multiple `include:` mechanisms. Never publish two separate `v=spf1` TXT records, this silently breaks SPF entirely (RFC 7208 treats it as a hard PermError). The admin panel's deliverability checker (below) explicitly detects and flags this.

**DMARC** tells receivers what to do when SPF/DKIM fail. Add one TXT record at `_dmarc.yourdomain.tld`:

```
v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@yourdomain.tld
```

- `p=none`: monitoring only, offers no actual protection (a stale leftover from initial DMARC rollout is common, so check this hasn't stayed at `none` for years).
- `p=quarantine`: failing mail goes to spam. Recommended starting point.
- `p=reject`: failing mail is rejected outright. Strongest, move here once `quarantine` hasn't caused issues with legitimate mail.

**DKIM** cryptographically signs outgoing mail. DKIM is configured and signed by *your SMTP provider*, not by iTransfer, which only relays through your authenticated SMTP account and does not sign messages itself. Enable it and find your selector in your provider's control panel:

| Provider | Where to enable DKIM |
|---|---|
| OVH | Web Cloud panel → Emails → DKIM (per-domain toggle) |
| Gmail / Google Workspace | Admin console → Apps → Google Workspace → Gmail → Authenticate email |
| Office 365 | Microsoft 365 Defender → Policies & rules → Email authentication settings → DKIM |

### Re-check periodically

DNS records drift: a registrar UI change can silently overwrite a TXT record, another service added later can introduce a second conflicting SPF record, or a DMARC policy set to `p=none` years ago may never have been tightened. "I checked this a while ago" is not the same as "this is correct right now." Use the **Check deliverability** button in the admin SMTP tab to re-run live SPF/DMARC/(optional DKIM) DNS lookups any time mail seems to be landing in spam, especially after any DNS or registrar change, and periodically even if nothing else changed.

## Languages

The interface and the notification emails are available in English, Français, Español, Deutsch and Italiano.

There is a single language per visitor: it is auto-detected from the browser on first visit, can be changed with the switcher in the header, and is remembered in the browser (per device). On the send page, that same language is used for the recipient notification, the upload confirmation, and the later download alert email. The download page always renders in the visitor's own language, never in the sender's.

No configuration is required. To add or adjust a language, edit the per-language JSON files in `frontend/src/i18n/` for the interface and the `TRANSLATIONS` dict in `backend/app/email_i18n.py` for the emails.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FRONTEND_URL` | yes | `http://localhost:3500` | Public frontend URL |
| `BACKEND_URL` | yes | `http://localhost:5500` | Public backend URL |
| `ADMIN_USERNAME` | yes | (none) | Admin login |
| `ADMIN_PASSWORD` | yes | (none) | Admin password |
| `DATABASE_URL` | yes | SQLite fallback | MariaDB connection string |
| `JWT_SECRET_KEY` | yes | random | JWT signing key, set a stable value |
| `TUS_HOOK_SECRET` | yes | `changeme-tus-hook-secret` | Shared secret the `tusd` service must present on every call to `/api/tus-hooks`; must match the value baked into `tusd`'s `-hooks-http` URL |
| `TIMEZONE` | no | `Europe/Paris` | Timezone for expiry display |
| `FORCE_HTTPS` | no | `true` | Enforce HTTPS in generated URLs |
| `PROXY_COUNT` | no | `1` | Number of reverse proxies in front |
| `GUNICORN_TIMEOUT` | no | `1800` | Worker heartbeat timeout (seconds); raise for very long transfers on slow links |
| `GUNICORN_WORKERS` | no | `4` | Gunicorn worker processes |
| `GUNICORN_THREADS` | no | `4` | Threads per worker (concurrent transfers per process) |

## Upgrading

Newer versions may add columns to the database schema automatically on startup (additive only, existing data is never dropped or rewritten). As with any schema change, back up `./db_data` before pulling a new image version.

## Troubleshooting

**Files not received / emails rejected, or landing in spam**

1. Open the admin panel → SMTP tab → **Check deliverability**. This runs live DNS lookups against your sender domain for SPF and DMARC (and DKIM if you supply your provider's selector), and explicitly calls out a missing record, a misconfigured DMARC policy, or the "multiple SPF records" mistake.
2. If the checker reports a problem, see [Domain authentication](#domain-authentication-spf-dkim-dmarc) above for exact record syntax per provider.
3. Re-run the checker after any DNS/registrar change, don't assume a past check is still valid; records can be overwritten by a registrar UI change or by another service adding a conflicting record.
4. Check the admin "Transfers" tab: each transfer shows per-notification send status (recipient / sender / download alert) with the last SMTP error on hover, so you can tell whether an email was actually attempted and what failed.

**Upload fails with "Network error" on large files (small files work)**

Almost always a reverse proxy rejecting the request body -- and since uploads go through the **frontend** hostname (`/files/`), check that proxy's config, not just the backend's. Raise `client_max_body_size`, set `proxy_request_buffering off`, and raise the proxy timeouts on both server blocks as described in [Large file uploads](#large-file-uploads). A dropped connection mid-upload should resume on its own (retries automatically for a short while); if it instead restarts from zero, confirm the outer proxy isn't buffering or rewriting the `/files/` requests.

**Upload fails with `500` / "permission denied" on `tusd`'s logs**

The official `tusd` image runs as a non-root user (uid 1000), but a freshly created volume or bind mount is owned by root, so `tusd` can't write to it. The `tusd-init` container in the example `docker-compose.yml` fixes this automatically on every `docker compose up`. If you're on an older compose file without it, fix it by hand once -- either directly on the host if you're using a bind mount:
```bash
sudo chown -R 1000:1000 <your bind-mounted path>
```
or, for a named volume, via a disposable container that mounts it:
```bash
docker run --rm -v <volume-name>:/data busybox chown -R 1000:1000 /data
```
then `docker compose restart tusd`.

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

GPL-3.0. See [LICENSE](LICENSE).

# iTransfer

A simple file transfer application with web interface, secure backend, and email notifications.

JUST FOR LOCAL USE FOR NOW. Will work on reverse proxying soon.

## Features

- Responsive user interface
- File upload with progress bar
- Automatic email notifications for both sender and recipient
- Secure admin interface
- REST API backend
- Easy deployment with Docker
- File management with MariaDB database

## Prerequisites

- Docker
- Docker Compose

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tiritibambix/iTransfer.git
cd iTransfer
```

2. Choose your deployment mode:

### Local Development
Use `docker-compose.local.yml` for local development:
```bash
docker compose -f docker-compose.local.yml up -d
```
This will:
- Start the frontend on http://localhost:3500
- Start the backend on http://localhost:5500
- Expose the database on port 3306 for development

### Production
Use `docker-compose.prod.yml` for production deployment:
```bash
docker compose -f docker-compose.prod.yml up -d
```
This requires:
- A reverse proxy (like Nginx or Traefik) configured for:
  - Frontend domain (e.g., itransfer.domain.com) on port 3500
  - Backend domain (e.g., api.itransfer.domain.com) on port 5500
- SSL certificates for both domains
- DNS configuration for both domains

### Configuration Files

#### Local Development (`docker-compose.local.yml`)
```yaml
frontend:
  environment:
    - BACKEND_URL=http://localhost:5500  # Local backend URL
  ports:
    - "3500:80"                         # Local frontend port

backend:
  environment:
    - FRONTEND_URL=http://localhost:3500 # Local frontend URL
  ports:
    - "5500:5000"                       # Local backend port
```

#### Production (`docker-compose.prod.yml`)
```yaml
frontend:
  environment:
    - BACKEND_URL=https://api.itransfer.domain.com  # Production API URL
  ports:
    - "3500:80"                                    # Production frontend port

backend:
  environment:
    - FRONTEND_URL=https://itransfer.domain.com     # Production frontend URL
  ports:
    - "5500:5000"                                  # Production backend port
```

### Port Configuration

The application uses consistent ports across environments:
- Frontend: Always runs on port 3500 (mapped to container port 80)
- Backend: Always runs on port 5500 (mapped to container port 5000)
- Database: Port 3306 (exposed in local development only)

### Switching Between Environments

1. Stop the current environment:
```bash
# If running local
docker compose -f docker-compose.local.yml down

# If running production
docker compose -f docker-compose.prod.yml down
```

2. Start the desired environment:
```bash
# For local development
docker compose -f docker-compose.local.yml up -d

# For production
docker compose -f docker-compose.prod.yml up -d
```

### Reverse Proxy Configuration (Production)

Your reverse proxy should be configured to:
1. Forward traffic from itransfer.domain.com to frontend:80 (listening on port 3500)
2. Forward traffic from api.itransfer.domain.com to backend:5000 (listening on port 5500)
3. Handle SSL termination for both domains
4. Forward the original protocol (HTTP/HTTPS) to the services

## [docker-compose.yml](https://github.com/tiritibambix/iTransfer/blob/main/docker-compose.yml)

Set up the database initialization file:
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

Then
```yaml
services:
  frontend:
    image: tiritibambix/itransfer-frontend
    ports:
      - "3500:80"
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
      - ADMIN_USERNAME=adminuser
      - ADMIN_PASSWORD=adminuserpassword
      - DATABASE_URL=mysql+mysqldb://mariadb_user:mariadb_pass@db/mariadb_db
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

## Configuration

### Environment Variables

The project uses several environment variables configurable in `docker-compose.yml`:

#### Frontend
- `BACKEND_URL`: Backend URL (default: http://localhost:5500)
  - For local development: use `http://localhost:PORT` where PORT matches your backend port
  - For production: use your domain (e.g., `https://api.yourdomain.com`)

#### Backend
- `FRONTEND_URL`: Frontend URL (default: http://localhost:3500)
- `ADMIN_USERNAME`: Admin username
- `ADMIN_PASSWORD`: Admin password
- `DATABASE_URL`: Database connection URL (using mysql+mysqldb driver)

#### Database
- `MYSQL_ROOT_PASSWORD`: MariaDB root password
- `MYSQL_DATABASE`: Database name
- `MYSQL_USER`: MariaDB user
- `MYSQL_PASSWORD`: MariaDB user password

### Port Configuration

The application uses several ports that can be configured in `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "3500:80"    # Change 3500 to your desired frontend port

backend:
  ports:
    - "5500:5000"  # Change 5500 to your desired backend port
    # Important: Make sure BACKEND_URL matches this port in local development
```

Remember to update the `BACKEND_URL` environment variable to match your backend port:
```yaml
frontend:
  environment:
    - BACKEND_URL=http://localhost:5500  # Match your backend port here
```

## Usage

1. Access the web interface: http://localhost:3500
2. To upload a file:
   - Drag and drop or select a file
   - Enter the recipient's email address
   - Enter your email address (sender)
   - Click "Send"
3. Both you and the recipient will receive email notifications:
   - Recipient gets a download link
   - You get a confirmation of upload
   - You'll be notified when the recipient downloads the file

## Administration

1. Access the admin interface: http://localhost:3500/admin
2. Log in with the configured credentials
3. Configure your SMTP settings to enable email notifications

## Project Structure

```
iTransfer/
├── LICENSE
├── README.md
├── backend
|      ├── Dockerfile
|      ├── app
|      |      ├── __init__.py
|      |      ├── app.py
|      |      ├── config.py
|      |      ├── models.py
|      |      ├── routes.py
|      ├── entrypoint.sh
|      ├── init.sql
|      ├── run.py
├── docker-compose.yml
├── frontend
|      ├── Dockerfile
|      ├── package.json
|      ├── public
|      |      ├── index.html
|      ├── src
|      |      ├── App.js
|      |      ├── Login.js
|      |      ├── PrivateRoute.js
|      |      ├── SMTPSettings.js
|      |      ├── index.css
|      |      ├── index.js
├── requirements.txt
```

## Troubleshooting

### Database Connection Issues
If you encounter database connection errors, ensure:
1. The database service is running: `docker-compose ps`
2. The database URL in `docker-compose.yml` uses the correct format:
   ```yaml
   DATABASE_URL=mysql+mysqldb://mariadb_user:mariadb_pass@db/mariadb_db
   ```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under The GNU General Public License - see the [LICENSE](LICENSE) file for details.
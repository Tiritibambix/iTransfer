[![Build and Push Docker Images](https://github.com/tiritibambix/iTransfer/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/tiritibambix/iTransfer/actions/workflows/docker-build-push.yml)

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

3. Start the containers:
```bash
docker-compose up -d
```
## [docker-compose.yml](https://github.com/tiritibambix/iTransfer/blob/main/docker-compose.yml)

Set up the database initialization file:
   - Either download [init.sql](https://github.com/tiritibambix/iTransfer/blob/main/backend/init.sql) and place it in `backend/init.sql`
   - Or create the file manually at `backend/init.sql`

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
|     ├── Dockerfile
|     ├── app
|     |     ├── __init__.py
|     |     ├── app.py
|     |     ├── config.py
|     |     ├── models.py
|     |     ├── routes.py
|     ├── entrypoint.sh
|     ├── init.sql
|     ├── run.py
├── docker-compose.yml
├── frontend
|     ├── Dockerfile
|     ├── package.json
|     ├── public
|     |     ├── index.html
|     ├── src
|     |     ├── App.js
|     |     ├── Login.js
|     |     ├── PrivateRoute.js
|     |     ├── SMTPSettings.js
|     |     ├── index.css
|     |     ├── index.js
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
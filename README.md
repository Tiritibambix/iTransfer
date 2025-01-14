# iTransfer

A simple file transfer application with web interface, secure backend, and email notifications.

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
|     ├── Dockerfile
|     ├── app
|     |     ├── __init__.py
|     |     ├── app.py
|     |     ├── config.py
|     |     ├── models.py
|     |     ├── routes.py
|     ├── entrypoint.sh
|     ├── init.sql
|     ├── run.py
├── docker-compose.yml
├── frontend
|     ├── Dockerfile
|     ├── package.json
|     ├── public
|     |     ├── index.html
|     ├── src
|     |     ├── App.js
|     |     ├── Login.js
|     |     ├── PrivateRoute.js
|     |     ├── SMTPSettings.js
|     |     ├── index.css
|     |     ├── index.js
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

This project is licensed under the MIT License - see the LICENSE file for details.
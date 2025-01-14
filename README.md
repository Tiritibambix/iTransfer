# iTransfer

Application de transfert de fichiers sécurisée

## Configuration Docker

### 1. Configuration locale (développement)

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    environment:
      - REACT_APP_API_URL=http://localhost:5000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules

  backend:
    build: ./backend
    environment:
      - FLASK_ENV=development
      - FLASK_APP=app
      - DATABASE_URL=postgresql://user:password@db:5432/itransfer
      - BEHIND_PROXY=False
      - CORS_ORIGINS=http://localhost:3000
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=itransfer
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Pour lancer l'application en local :
```bash
docker-compose up --build
```

L'application sera accessible sur :
- Frontend : http://localhost:3000
- Backend : http://localhost:5000

### 2. Configuration avec Nginx Proxy Manager (production)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build: 
      context: ./frontend
      args:
        - REACT_APP_API_URL=/api  # Le backend sera accessible via /api
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - npm_network

  backend:
    build: ./backend
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app
      - DATABASE_URL=postgresql://user:password@db:5432/itransfer
      - BEHIND_PROXY=True
      - PREFERRED_URL_SCHEME=https
      - CORS_ORIGINS=https://itransfer.votredomaine.com
    restart: unless-stopped
    networks:
      - npm_network
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=itransfer
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - npm_network

networks:
  npm_network:
    external: true  # Ce réseau doit être créé manuellement et partagé avec NPM

volumes:
  postgres_data:
```

#### Configuration de Nginx Proxy Manager

1. Créez d'abord le réseau Docker partagé :
```bash
docker network create npm_network
```

2. Dans l'interface de NPM, créez un nouveau "Proxy Host" :
   - Domain: itransfer.votredomaine.com
   - Scheme: https
   - Forward Hostname: frontend
   - Forward Port: 3000
   - Configuration personnalisée :
   ```nginx
   location /api/ {
       proxy_pass http://backend:5000/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_cache_bypass $http_upgrade;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

3. Activez SSL pour votre domaine dans NPM

4. Lancez l'application :
```bash
docker-compose -f docker-compose.prod.yml up -d
```

L'application sera accessible sur :
- https://itransfer.votredomaine.com

### Notes importantes

1. En production :
   - Changez les identifiants de base de données
   - Utilisez des secrets Docker pour les mots de passe
   - Configurez correctement les pare-feu
   - Activez les sauvegardes de la base de données

2. Pour la mise à jour :
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

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
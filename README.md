[![Build and Push Docker Images](https://github.com/tiritibambix/iTransfer/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/tiritibambix/iTransfer_1minAI/actions/workflows/docker-build-push.yml)

# iTransfer

Une application moderne de transfert de fichiers avec interface web, backend sécurisé et notification par email.

## Fonctionnalités

- Interface utilisateur moderne et réactive
- Upload de fichiers avec barre de progression
- Notifications par email automatiques
- Interface d'administration sécurisée
- API REST backend
- Déploiement facile avec Docker
- Gestion des fichiers avec base de données MariaDB

## Prérequis

- Docker
- Docker Compose
- Accès aux ports 3500 (frontend), 5500 (backend) et 3306 (MariaDB)

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-username/iTransfer.git
cd iTransfer
```

2. Créez le fichier d'initialisation SQL :
```bash
# Créez le fichier init.sql dans le dossier spécifié
mkdir -p /srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/backend/
cat > /srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/backend/init.sql << EOL
CREATE TABLE IF NOT EXISTS file_upload (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    encrypted_data VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOL
```

3. Démarrez les conteneurs :
```bash
docker-compose up -d
```

## Configuration

### Variables d'environnement

Le projet utilise plusieurs variables d'environnement configurables dans le `docker-compose.yml` :

#### Backend
- `FRONTEND_URL`: URL du frontend (par défaut: http://localhost:3500)
- `ADMIN_USERNAME`: Nom d'utilisateur admin
- `ADMIN_PASSWORD`: Mot de passe admin
- `DATABASE_URL`: URL de connexion à la base de données

#### Base de données
- `MYSQL_ROOT_PASSWORD`: Mot de passe root MariaDB
- `MYSQL_DATABASE`: Nom de la base de données
- `MYSQL_USER`: Utilisateur MariaDB
- `MYSQL_PASSWORD`: Mot de passe utilisateur MariaDB

### Configuration SMTP

La configuration SMTP peut être effectuée via l'interface d'administration :
1. Connectez-vous à l'interface admin (http://localhost:3500/admin)
2. Accédez aux paramètres SMTP
3. Configurez les détails de votre serveur SMTP

## Structure des volumes

Le projet utilise plusieurs volumes Docker pour la persistance des données :

- `/srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/db_data`: Données MariaDB
- `/srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/backend/init.sql`: Script d'initialisation SQL
- `/srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/backend_data`: Données du backend
- `/srv/dev-disk-by-uuid-7fe66601-5ca0-4c09-bc13-a015025fe53a/Files/iTransfer/uploads`: Fichiers uploadés

## Utilisation

1. Accédez à l'interface web : http://localhost:3500
2. Pour uploader un fichier :
   - Glissez-déposez ou sélectionnez un fichier
   - Entrez l'adresse email du destinataire
   - Cliquez sur "Envoyer"
3. Le destinataire recevra un email avec les informations de téléchargement

## Administration

1. Accédez à l'interface admin : http://localhost:3500/admin
2. Connectez-vous avec les identifiants configurés
3. Gérez les paramètres SMTP et autres configurations

## Ports utilisés

- Frontend: 3500
- Backend: 5500
- MariaDB: 3306

## Sécurité

- Authentification admin sécurisée
- Chiffrement des données des fichiers
- Validation des emails
- Healthcheck de la base de données

## Développement

Pour le développement local sans Docker :

### Backend (Python/Flask)
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend (React)
```bash
cd frontend
npm install
npm start
```
```
├── .github
|      ├── dependabot.yml
|      ├── workflows
|      |      ├── docker-build-push.yml
├── LICENSE
├── README.md
├── backend
|      ├── Dockerfile
|      ├── entrypoint.sh
|      ├── app
|      |      ├── __init__.py
|      |      ├── app.py
|      |      ├── config.py
|      |      ├── models.py
|      |      ├── routes.py
|      |      ├── utils.py
|      ├── run.py
|      ├── tests
|      |      ├── test_routes.py
├── docker-compose.yml
├── frontend
|      ├── Dockerfile
|      ├── package.json
|      ├── public
|      |      ├── index.html
|      ├── src
|      |      ├── Admin.js
|      |      ├── App.js
|      |      ├── FileManager.js
|      |      ├── Login.js
|      |      ├── PrivateRoute.js
|      |      ├── Progress.js
|      |      ├── ProgressBar.js
|      |      ├── Settings.js
|      |      ├── Uploads.js
|      |      ├── index.css
|      |      ├── index.js
├── requirements.txt
```
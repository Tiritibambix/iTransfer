-- Donner tous les privilèges à l'utilisateur mariadb_user depuis n'importe quel hôte
GRANT ALL PRIVILEGES ON mariadb_db.* TO 'mariadb_user'@'%' IDENTIFIED BY 'mariadb_pass';
FLUSH PRIVILEGES;

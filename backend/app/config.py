import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://mariadb_user:mariadb_pass@db/mariadb_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = os.environ.get('SMTP_PORT')
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'adminuser'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'adminuserpassword'

import os
import secrets


def _abs(path: str) -> str:
    """Return an absolute, symlink-resolved path."""
    return os.path.realpath(os.path.abspath(path))


class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Secrets
    # SECRET_KEY should be provided via env for session stability across restarts.
    # A random fallback is only used in development.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', '24'))

    # Timezone
    TIMEZONE = os.environ.get('TIMEZONE', 'Europe/Paris')

    # Paths (resolved to absolute form so path-validation checks are reliable)
    UPLOAD_FOLDER = _abs(
        os.environ.get('UPLOAD_FOLDER')
        or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    )
    DATA_FOLDER = _abs(
        os.environ.get('DATA_FOLDER')
        or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    )
    SMTP_CONFIG_PATH = _abs(
        os.environ.get('SMTP_CONFIG_PATH')
        or os.path.join(DATA_FOLDER, 'smtp_config.json')
    )

    # Enforce that SMTP_CONFIG_PATH lives inside DATA_FOLDER. This hardens any
    # future code path that might read/write it based on user input.
    if not SMTP_CONFIG_PATH.startswith(DATA_FOLDER + os.sep):
        raise RuntimeError("SMTP_CONFIG_PATH must be inside DATA_FOLDER")

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 * 1024  # 50 GB

    # Shared secret the tusd service must present (as a query string on the
    # -hooks-http URL) on every call to /api/tus-hooks, so that endpoint
    # can't be driven by an arbitrary caller on the docker network or the
    # backend's published host port. Not a per-session credential, just
    # proof the caller is the configured tusd instance.
    TUS_HOOK_SECRET = os.environ.get('TUS_HOOK_SECRET', 'changeme-tus-hook-secret')

    # Root of tusd's own filestore (the `-upload-dir` tusd is started with).
    # Must match the path inside *this* container where the same named
    # volume is mounted -- see docker-compose.yml. Used only to sanity-check
    # paths reported by the post-finish hook before touching them.
    TUSD_DATA_DIR = os.environ.get('TUSD_DATA_DIR', '/data')

    # Admin credentials (no defaults: failing closed is safer than shipping
    # known credentials).
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

    # HTTPS / proxy
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'
    PROXY_COUNT = int(os.environ.get('PROXY_COUNT', '1'))
    PREFERRED_URL_SCHEME = 'https' if FORCE_HTTPS else 'http'

    # Ensure folders exist with tight permissions
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)

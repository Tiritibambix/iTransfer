"""
iTransfer backend application.

Single source of truth for the Flask app instance. The app is initialised
at module import time (not inside a factory) so that ``package.app`` is a
resolvable attribute before ``routes`` is imported. This sidesteps
Python's ``from package import name`` submodule-precedence rule: even if a
stale ``app.py`` sits in this directory, ``from . import app`` still
resolves to this module's ``app`` attribute because it already exists on
the package when routes is loaded.
"""
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler

import schedule
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc, inspect, text
from werkzeug.exceptions import HTTPException


# -------------------------------------------------------------------------
# App + extensions
# -------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object('app.config.Config')

db = SQLAlchemy(app)


# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
def _configure_logging(flask_app: Flask) -> None:
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'itransfer.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    flask_app.logger.handlers.clear()
    flask_app.logger.addHandler(file_handler)
    flask_app.logger.addHandler(console_handler)
    flask_app.logger.setLevel(logging.INFO)


_configure_logging(app)
app.logger.info('iTransfer backend startup')


# -------------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------------
_frontend_url = os.environ.get('FRONTEND_URL', '').rstrip('/')
if os.environ.get('ALLOW_CORS_WILDCARD', '').lower() == 'true':
    _origins = '*'
elif _frontend_url:
    _origins = [_frontend_url]
else:
    _origins = []
CORS(
    app,
    resources={r"/*": {"origins": _origins}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    supports_credentials=False,
)


# -------------------------------------------------------------------------
# DB readiness
# -------------------------------------------------------------------------
def _wait_for_db(max_retries: int = 10, delay: int = 2) -> None:
    current_delay = delay
    for attempt in range(1, max_retries + 1):
        try:
            with db.engine.connect():
                app.logger.info("Database connection established")
                return
        except exc.OperationalError:
            if attempt == max_retries:
                app.logger.exception("Database unreachable after %d attempts", max_retries)
                raise
            app.logger.warning(
                "DB connection attempt %d/%d failed, retrying in %ds",
                attempt, max_retries, current_delay,
            )
            time.sleep(current_delay)
            current_delay = min(current_delay * 2, 30)


def _ensure_notification_columns() -> None:
    """Idempotently add notification-tracking columns to file_upload for
    instances upgrading from a schema that predates this feature.
    db.create_all() only creates missing tables, it never alters existing
    ones, so this defensive step is required on every startup. Each ALTER
    is additive-only (nullable, no data rewrite) and individually
    existence-checked, so it is safe to run unconditionally and repeatedly.
    """
    inspector = inspect(db.engine)
    if 'file_upload' not in inspector.get_table_names():
        return  # create_all() just made it fresh with all columns already

    wanted = {
        'notification_status_recipient': 'VARCHAR(16)',
        'notification_error_recipient': 'VARCHAR(500)',
        'notification_status_sender': 'VARCHAR(16)',
        'notification_error_sender': 'VARCHAR(500)',
        'notification_status_download': 'VARCHAR(16)',
        'notification_error_download': 'VARCHAR(500)',
    }

    is_mysql = db.engine.dialect.name in ('mysql', 'mariadb')
    lock_acquired = False
    try:
        if is_mysql:
            # Guard against the 4 Gunicorn worker processes racing to ALTER
            # the same table concurrently at startup.
            with db.engine.connect() as conn:
                lock_acquired = bool(conn.execute(
                    text("SELECT GET_LOCK('itransfer_schema_migration', 10)")
                ).scalar())

        # Re-inspect after acquiring the lock: another worker may have
        # already finished the migration while we waited.
        existing = {col['name'] for col in inspect(db.engine).get_columns('file_upload')}
        missing = {name: ddl for name, ddl in wanted.items() if name not in existing}
        if not missing:
            return

        for name, ddl in missing.items():
            try:
                with db.engine.begin() as conn:
                    app.logger.info("Migrating schema: adding column %s to file_upload", name)
                    conn.execute(text(f"ALTER TABLE file_upload ADD COLUMN {name} {ddl} DEFAULT NULL"))
            except exc.OperationalError:
                # Another worker process won the race despite the advisory
                # lock (e.g. GET_LOCK timed out under heavy contention) and
                # already added this column -- not a real failure.
                app.logger.info("Column %s already exists, skipping", name)
    finally:
        if lock_acquired:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT RELEASE_LOCK('itransfer_schema_migration')"))


with app.app_context():
    _wait_for_db()
    from . import models  # noqa: F401  (register models before create_all)
    db.create_all()
    _ensure_notification_columns()


# -------------------------------------------------------------------------
# Global error handlers (no stack trace ever reaches clients)
# -------------------------------------------------------------------------
@app.errorhandler(HTTPException)
def _handle_http(error):
    response = jsonify({'error': error.description})
    response.status_code = error.code
    return response


@app.errorhandler(Exception)
def _handle_unexpected(error):
    app.logger.exception("Unhandled exception")
    return jsonify({'error': 'An internal error has occurred'}), 500


# -------------------------------------------------------------------------
# Background email executor
# -------------------------------------------------------------------------
# Bounds concurrent SMTP connections per worker process (this is one pool
# per Gunicorn worker, not shared across the 4 worker processes -- fine at
# this app's volume, see notification dispatch in routes.py). A bounded
# pool (rather than a bare thread per email) caps how many concurrent
# connections get opened against the self-hoster's SMTP relay account if
# uploads burst, which several providers rate-limit or temp-block on.
# Defined before importing routes, which imports this module by name.
email_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='itransfer-mail')


# -------------------------------------------------------------------------
# Routes (registered via side-effect import)
# -------------------------------------------------------------------------
from . import routes  # noqa: E402,F401


# -------------------------------------------------------------------------
# Background scheduler for expired-file cleanup
# -------------------------------------------------------------------------
def _cleanup_expired_files() -> None:
    from datetime import datetime
    from .models import FileUpload
    try:
        expired = FileUpload.query.filter(
            FileUpload.expires_at < datetime.utcnow()
        ).all()
        upload_root = os.path.realpath(app.config['UPLOAD_FOLDER'])
        for record in expired:
            try:
                candidate = os.path.realpath(
                    os.path.join(app.config['UPLOAD_FOLDER'], record.filename)
                )
                if (
                    candidate == upload_root
                    or not candidate.startswith(upload_root + os.sep)
                ):
                    app.logger.warning(
                        "Refusing to delete %s (outside upload folder)", record.id
                    )
                elif os.path.exists(candidate):
                    os.remove(candidate)
                    app.logger.info("Removed expired file %s", record.id)
                db.session.delete(record)
            except Exception:
                app.logger.exception("Failed to remove expired file %s", record.id)
        db.session.commit()
    except Exception:
        app.logger.exception("Cleanup task failed")


def _run_scheduler() -> None:
    with app.app_context():
        # Run once at startup to catch files that expired while the container was down.
        _cleanup_expired_files()
        schedule.every(12).hours.do(_cleanup_expired_files)
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute so scheduled jobs fire on time


threading.Thread(target=_run_scheduler, daemon=True, name='itransfer-cleanup').start()

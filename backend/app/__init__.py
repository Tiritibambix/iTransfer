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
from logging.handlers import RotatingFileHandler

import schedule
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
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


with app.app_context():
    _wait_for_db()
    from . import models  # noqa: F401  (register models before create_all)
    db.create_all()


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

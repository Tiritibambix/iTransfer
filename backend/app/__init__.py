"""
iTransfer backend application factory.

Single source of truth for the Flask app instance. The previous layout had
both __init__.py and app.py creating apps; routes registered in routes.py
were attached to one while gunicorn served the other. Everything now lives
here.
"""
import os
import logging
import time
import threading
from logging.handlers import RotatingFileHandler

import schedule
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()


def _configure_logging(app: Flask) -> None:
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

    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)


def _wait_for_db(app: Flask, max_retries: int = 10, delay: int = 2) -> None:
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


def _register_error_handlers(app: Flask) -> None:
    """
    Global error handlers that guarantee no stack trace ever reaches clients.
    CodeQL py/stack-trace-exposure fires whenever an exception (or str(e),
    traceback.format_exc(), etc.) flows into a Flask response. Funnelling
    everything through these handlers keeps the server log verbose and the
    client response generic.
    """
    @app.errorhandler(HTTPException)
    def _handle_http(error):
        response = jsonify({'error': error.description})
        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def _handle_unexpected(error):
        app.logger.exception("Unhandled exception")
        return jsonify({'error': 'An internal error has occurred'}), 500


def _start_scheduler(app: Flask) -> None:
    from datetime import datetime
    from .models import FileUpload

    def cleanup_expired_files():
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
                    # Defence in depth: never touch anything outside UPLOAD_FOLDER
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

    def _run():
        with app.app_context():
            schedule.every(12).hours.do(cleanup_expired_files)
            while True:
                schedule.run_pending()
                time.sleep(3600)

    threading.Thread(target=_run, daemon=True, name='itransfer-cleanup').start()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    _configure_logging(app)
    app.logger.info('iTransfer backend startup')

    frontend_url = os.environ.get('FRONTEND_URL', '').rstrip('/')
    if os.environ.get('ALLOW_CORS_WILDCARD', '').lower() == 'true':
        origins = '*'
    elif frontend_url:
        origins = [frontend_url]
    else:
        origins = []
    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        supports_credentials=False,
    )

    db.init_app(app)

    with app.app_context():
        _wait_for_db(app)
        from . import models  # noqa: F401
        db.create_all()

    _register_error_handlers(app)

    from . import routes  # noqa: F401
    _start_scheduler(app)
    return app


# WSGI entry point (gunicorn "app:app")
app = create_app()

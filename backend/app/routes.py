"""
HTTP routes.

Security posture:
* No client-facing response ever contains ``str(exc)`` or ``traceback`` data.
  All error replies are generic strings; full diagnostic info goes to the
  server log via ``logger.exception``.
* Every filesystem path derived from user input is routed through
  ``paths.safe_join`` / ``paths.safe_stored_filename`` which validate the
  result stays inside the configured root directory.
* Protected endpoints require a JWT issued by /login.
* SMTP credentials are never logged.
"""
import hashlib
import json
import os
import shutil
import smtplib
import uuid
import zipfile
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

import pytz
from flask import current_app, jsonify, request, send_from_directory

from . import app, db
from .auth import issue_token, require_auth
from .models import FileUpload
from .paths import UnsafePathError, safe_join, safe_stored_filename


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
def format_size(num_bytes: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def _load_smtp_config():
    """Return parsed SMTP config, or raise FileNotFoundError."""
    path = app.config['SMTP_CONFIG_PATH']
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def _safe_smtp_config_summary(cfg: dict) -> dict:
    """Return a copy of cfg safe to log (password redacted)."""
    redacted = {k: v for k, v in cfg.items() if k != 'smtp_password'}
    redacted['smtp_password'] = '***redacted***'
    return redacted


def send_email_with_smtp(msg, smtp_config) -> bool:
    server = None
    try:
        port = int(smtp_config['smtp_port'])
        if port == 465:
            app.logger.info("Sending via SMTP_SSL on port %d", port)
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port)
        else:
            app.logger.info("Sending via SMTP+STARTTLS on port %d", port)
            server = smtplib.SMTP(smtp_config['smtp_server'], port)
            server.starttls()
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
        server.send_message(msg)
        return True
    except Exception:
        app.logger.exception("SMTP send failed")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                app.logger.exception("Error closing SMTP connection")


def get_backend_url() -> str:
    backend_url = os.environ.get('BACKEND_URL')
    if backend_url:
        if app.config['FORCE_HTTPS']:
            if backend_url.startswith('http://'):
                backend_url = 'https://' + backend_url[len('http://'):]
            elif not backend_url.startswith('https://'):
                backend_url = 'https://' + backend_url
        return backend_url
    if not request:
        proto = 'https' if app.config['FORCE_HTTPS'] else 'http'
        return f'{proto}://localhost:5500'
    proto = 'https' if app.config['FORCE_HTTPS'] else request.scheme
    if app.config['PROXY_COUNT'] > 0 and request.headers.get('X-Forwarded-Proto'):
        proto = request.headers.get('X-Forwarded-Proto')
    host = request.headers.get('Host', 'localhost:5500')
    return f"{proto}://{host}"


def create_email_template(title, message, file_summary, total_size, download_link=None):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; line-height: 1.6; color: #170017; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 20px auto; padding: 0; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); }}
            .header {{ text-align: center; padding: 30px 0; background: #693a67; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: 0.5px; }}
            .content {{ padding: 30px; background-color: #ffffff; }}
            .message h2 {{ color: #693a67; margin: 0 0 15px 0; font-size: 22px; font-weight: 500; }}
            .files {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; white-space: pre-wrap; color: #170017; border: 1px solid rgba(0, 0, 0, 0.05); margin: 20px 0; line-height: 1.8; font-size: 15px; }}
            .total {{ margin-top: 20px; padding: 15px 20px; background-color: #693a67; color: #ffffff; border-radius: 8px; font-weight: 500; font-size: 16px; }}
            .footer {{ text-align: center; padding: 20px; color: #5a4e5a; font-size: 14px; border-top: 1px solid rgba(0, 0, 0, 0.05); }}
            .download-btn {{ display: inline-block; margin: 20px 0; padding: 12px 24px; background-color: #693a67; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 500; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>iTransfer</h1></div>
            <div class="content">
                <div class="message"><h2>{title}</h2><p>{message}</p></div>
                {f'<a href="{download_link}" class="download-btn">Telecharger les fichiers</a>' if download_link else ''}
                <div class="files">{file_summary}</div>
                <div class="total">{total_size}</div>
            </div>
            <div class="footer"><p>Envoye via iTransfer</p></div>
        </div>
    </body>
    </html>
    """
    text = (
        f"{title}\n\n{message}\n\n"
        f"{'Lien de telechargement : ' + download_link if download_link else ''}\n\n"
        f"Resume des fichiers :\n{file_summary}\n\nTaille totale : {total_size}\n"
    )
    return html, text


def _send_recipient_notification(recipient_email, file_id, files_summary, total_size, smtp_config, sender_email):
    try:
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            app.logger.error("File not found for notification: %s", file_id)
            return False

        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        expiration_formatted = file_info.expires_at.astimezone(tz).strftime('%d/%m/%Y a %H:%M:%S')

        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{file_id}"

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = recipient_email
        msg['Subject'] = f"{sender_email} vous envoie des fichiers"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        title = "Vous avez recu des fichiers"
        message = (
            f"{sender_email} vous a envoye des fichiers. Cliquez sur le bouton "
            f"ci-dessous pour acceder a la page de telechargement.<br><br>"
            f"Ce lien expirera le {expiration_formatted}"
        )
        html, text = create_email_template(title, message, files_summary, total_size, download_page_link)
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        return send_email_with_smtp(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare recipient notification")
        return False


def _send_sender_confirmation(sender_email, file_id, files_list, total_size, smtp_config, recipient_email):
    try:
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{file_id}"

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Subject'] = f"Confirmation de votre transfert a {recipient_email}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        files_summary = ""
        for f in files_list:
            files_summary += f"- {f['name']} ({format_size(f['size'])})\n"

        title = "Vos fichiers ont ete envoyes"
        message = (
            f"Vos fichiers ont ete envoyes a : {recipient_email}<br><br>"
            f"Page de telechargement : {download_page_link}"
        )
        html, text = create_email_template(title, message, files_summary, total_size)
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        return send_email_with_smtp(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare sender confirmation")
        return False


def _send_download_notification(sender_email, file_id, smtp_config):
    try:
        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        download_time = datetime.now(tz).strftime('%d/%m/%Y a %H:%M:%S (%Z)')
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            app.logger.error("File not found for download notification: %s", file_id)
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Vos fichiers ont ete telecharges"
        msg['From'] = formataddr(("iTransfer", smtp_config.get('smtp_sender_email', '')))
        msg['To'] = sender_email
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        files_list = file_info.get_files_list()
        if files_list:
            total = sum(f['size'] for f in files_list)
            files_summary = "".join(
                f"- {f['name']} ({format_size(f['size'])})\n" for f in files_list
            )
            total_formatted = format_size(total)
        else:
            stored_name = safe_stored_filename(file_info.filename)
            stored_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
            size = os.path.getsize(stored_path)
            files_summary = f"- {stored_name} ({format_size(size)})"
            total_formatted = format_size(size)

        title = "Vos fichiers ont ete telecharges"
        message = f"Vos fichiers ont ete telecharges le {download_time}."
        html, text = create_email_template(title, message, files_summary, total_formatted)
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        return send_email_with_smtp(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to send download notification")
        return False


# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200

    data = request.get_json(silent=True) or {}
    username = data.get('username', '')
    password = data.get('password', '')
    expected_user = app.config.get('ADMIN_USERNAME')
    expected_pass = app.config.get('ADMIN_PASSWORD')

    if not expected_user or not expected_pass:
        app.logger.error("Admin credentials not configured; refusing all logins")
        return jsonify({'error': 'Server not configured'}), 503

    if username == expected_user and password == expected_pass:
        return jsonify({'token': issue_token(username)}), 200
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/upload', methods=['POST', 'OPTIONS'])
@require_auth
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200

    upload_root = app.config['UPLOAD_FOLDER']
    temp_dir = None
    zip_path = None
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        email = request.form.get('email')
        sender_email = request.form.get('sender_email')
        try:
            expiration_days = int(request.form.get('expiration_days', '7'))
        except ValueError:
            expiration_days = 7
        if expiration_days not in (3, 5, 7, 10):
            expiration_days = 7

        if not email or not sender_email:
            return jsonify({'error': 'Email addresses are required'}), 400

        try:
            files_list = json.loads(request.form.get('files_list', '[]'))
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid files_list payload'}), 400
        if not files_list:
            return jsonify({'error': 'Empty files_list'}), 400

        total_size = sum(int(f.get('size', 0)) for f in files_list)

        file_id = str(uuid.uuid4())
        # temp dir name is a UUID, no user input
        temp_dir = os.path.join(upload_root, 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)

        file_list = []
        for uploaded_file, raw_path in zip(files, paths):
            if not uploaded_file.filename:
                continue
            try:
                # The candidate is resolved inside temp_dir, never above it.
                # paths.safe_join fully sanitises raw_path (CodeQL sanitiser).
                target_path = safe_join(temp_dir, raw_path)
            except UnsafePathError:
                app.logger.warning("Rejected unsafe upload path")
                return jsonify({'error': 'Invalid file path'}), 400

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            uploaded_file.save(target_path)
            file_list.append({
                'relative': os.path.relpath(target_path, temp_dir).replace(os.sep, '/'),
                'size': os.path.getsize(target_path),
                'abs': target_path,
            })

        if not file_list:
            return jsonify({'error': 'No valid files uploaded'}), 400

        needs_zip = len(file_list) > 1 or any('/' in f['relative'] for f in file_list)

        if needs_zip:
            date_str = datetime.utcnow().strftime("%y%m%d%H%M%S")
            final_filename = f"iTransfer_{date_str}_{file_id[:8]}.zip"
            zip_path = safe_join(upload_root, final_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for entry in file_list:
                    zf.write(entry['abs'], entry['relative'])
            final_path = zip_path
        else:
            only = file_list[0]
            final_filename = safe_stored_filename(only['relative'])
            final_path = safe_join(upload_root, final_filename)
            shutil.move(only['abs'], final_path)

        with open(final_path, 'rb') as fh:
            file_hash = hashlib.sha256(fh.read()).hexdigest()

        original_files = [{'name': f['name'], 'size': int(f['size'])} for f in files_list]

        record = FileUpload(
            id=file_id,
            filename=final_filename,
            email=email,
            sender_email=sender_email,
            encrypted_data=file_hash,
            downloaded=False,
            expires_at=datetime.utcnow() + timedelta(days=expiration_days),
        )
        record.set_files_list(original_files)
        db.session.add(record)
        db.session.commit()

        files_summary = "".join(
            f"- {f['name']} ({format_size(f['size'])})\n" for f in original_files
        )
        total_formatted = format_size(total_size)

        notification_errors = []
        try:
            smtp_config = _load_smtp_config()
            if not _send_recipient_notification(
                email, file_id, files_summary, total_formatted, smtp_config, sender_email
            ):
                notification_errors.append("destinataire")
            if not _send_sender_confirmation(
                sender_email, file_id, original_files, total_formatted, smtp_config, email
            ):
                notification_errors.append("expediteur")
        except FileNotFoundError:
            app.logger.error("SMTP config missing, skipping notifications")
            notification_errors.append("smtp non configure")
        except Exception:
            app.logger.exception("Notification dispatch failed")
            notification_errors.append("erreur interne")

        response = {'success': True, 'file_id': file_id, 'message': 'Upload OK'}
        if notification_errors:
            response['warning'] = (
                "Notifications non envoyees : " + ", ".join(notification_errors)
            )
        return jsonify(response), 200

    except UnsafePathError:
        app.logger.warning("Unsafe path in upload request")
        return jsonify({'error': 'Invalid file path'}), 400
    except Exception:
        app.logger.exception("Upload failed")
        if zip_path and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                app.logger.exception("Could not remove partial zip")
        return jsonify({'error': 'Upload failed'}), 500
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/transfer/<file_id>', methods=['GET'])
def get_transfer_details(file_id):
    try:
        record = FileUpload.query.get(file_id)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        if datetime.utcnow() > record.expires_at:
            return jsonify({'error': 'Link expired'}), 410

        # Verify the stored file still exists on disk, routed through
        # safe_join to guarantee the lookup stays inside UPLOAD_FOLDER.
        stored_name = safe_stored_filename(record.filename)
        file_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File missing on server'}), 404

        files_list = record.get_files_list()
        if not files_list:
            files_list = [{'name': stored_name, 'size': os.path.getsize(file_path)}]

        return jsonify({
            'files': files_list,
            'expires_at': record.expires_at.isoformat(),
        }), 200
    except UnsafePathError:
        app.logger.warning("Unsafe stored filename for %s", file_id)
        return jsonify({'error': 'Not found'}), 404
    except Exception:
        app.logger.exception("transfer details failed")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        record = FileUpload.query.get(file_id)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        if datetime.utcnow() > record.expires_at:
            return jsonify({'error': 'Link expired'}), 410

        stored_name = safe_stored_filename(record.filename)
        # safe_join is the CodeQL sanitiser: stored_name is rebuilt from basename
        # and rejected if it contains anything beyond [A-Za-z0-9._-].
        file_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File missing on server'}), 404

        if not record.downloaded:
            record.downloaded = True
            db.session.commit()
            try:
                smtp_config = _load_smtp_config()
                _send_download_notification(record.sender_email, file_id, smtp_config)
            except FileNotFoundError:
                app.logger.info("SMTP not configured, skipping download notification")
            except Exception:
                app.logger.exception("Failed to send download notification")

        # send_from_directory performs its own path traversal check against
        # the directory argument. Passing stored_name (already sanitised)
        # makes this the belt-and-braces version.
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            stored_name,
            as_attachment=True,
            download_name=stored_name,
        )
    except UnsafePathError:
        app.logger.warning("Unsafe stored filename in download for %s", file_id)
        return jsonify({'error': 'Not found'}), 404
    except Exception:
        app.logger.exception("Download failed")
        return jsonify({'error': 'Download failed'}), 500


@app.route('/api/save-smtp-settings', methods=['POST', 'OPTIONS'])
@require_auth
def save_smtp_settings():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        data = request.get_json(silent=True) or {}
        required = ['smtpServer', 'smtpPort', 'smtpUser', 'smtpPassword', 'smtpSenderEmail']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Missing field: {field}'}), 400

        smtp_config = {
            'smtp_server': data['smtpServer'],
            'smtp_port': data['smtpPort'],
            'smtp_user': data['smtpUser'],
            'smtp_password': data['smtpPassword'],
            'smtp_sender_email': data['smtpSenderEmail'],
        }
        # Log only a redacted view (no password)
        app.logger.info("SMTP config updated: %s", _safe_smtp_config_summary(smtp_config))

        # SMTP_CONFIG_PATH is validated at Config load time to live inside
        # DATA_FOLDER, so writing to it cannot escape that directory.
        config_path = app.config['SMTP_CONFIG_PATH']
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as fh:
            json.dump(smtp_config, fh, indent=2)

        return jsonify({'message': 'SMTP config saved'}), 200
    except Exception:
        app.logger.exception("Failed to save SMTP config")
        return jsonify({'error': 'Could not save SMTP config'}), 500


@app.route('/api/test-smtp', methods=['POST', 'OPTIONS'])
@require_auth
def test_smtp():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        try:
            smtp_config = _load_smtp_config()
        except FileNotFoundError:
            return jsonify({'error': 'SMTP config not found'}), 404
        app.logger.info(
            "Testing SMTP: %s", _safe_smtp_config_summary(smtp_config)
        )

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("iTransfer", smtp_config['smtp_sender_email']))
        msg['To'] = smtp_config['smtp_sender_email']
        msg['Subject'] = "Test de configuration SMTP"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()
        msg.attach(MIMEText("Test SMTP iTransfer.", 'plain'))
        msg.attach(MIMEText("<p>Test SMTP iTransfer.</p>", 'html'))

        if send_email_with_smtp(msg, smtp_config):
            return jsonify({'message': 'SMTP test OK'}), 200
        return jsonify({'error': 'SMTP test failed'}), 500
    except Exception:
        app.logger.exception("SMTP test error")
        return jsonify({'error': 'SMTP test failed'}), 500

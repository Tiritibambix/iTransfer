"""
HTTP routes.

Security posture:
* No client-facing response ever contains ``str(exc)`` or ``traceback`` data.
* Every filesystem path derived from user input is routed through
  ``paths.safe_join`` / ``paths.safe_stored_filename``.
* Protected endpoints require a JWT issued by /login.
* SMTP credentials are never logged.
* Rate limiting via in-process token bucket (no Redis dependency).
* Recipient/sender emails are validated before any processing.
"""
import hashlib
import json
import os
import re
import shutil
import smtplib
import threading
import time
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
import pytz
from flask import Response, current_app, jsonify, request, send_from_directory, stream_with_context

from . import app, db
from .auth import issue_token, require_auth
from .models import FileUpload
from .paths import UnsafePathError, safe_join, safe_stored_filename


# -------------------------------------------------------------------------
# Rate limiting (token bucket, in-process)
# -------------------------------------------------------------------------
_rate_buckets: dict[str, dict] = defaultdict(lambda: {'tokens': 10, 'last': time.monotonic()})
_rate_lock = threading.Lock()

RATE_LIMIT_UPLOAD = 5      # requests
RATE_LIMIT_WINDOW = 60     # seconds
RATE_LIMIT_LOGIN  = 10


def _rate_limit(key: str, limit: int = RATE_LIMIT_UPLOAD, window: int = RATE_LIMIT_WINDOW) -> bool:
    """Return True if the request is allowed, False if rate-limited."""
    with _rate_lock:
        bucket = _rate_buckets[key]
        now = time.monotonic()
        elapsed = now - bucket['last']
        bucket['tokens'] = min(limit, bucket['tokens'] + elapsed * (limit / window))
        bucket['last'] = now
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        return False


def _client_key() -> str:
    """Best-effort client identifier for rate limiting."""
    if app.config['PROXY_COUNT'] > 0:
        forwarded = request.headers.get('X-Forwarded-For', '')
        ip = forwarded.split(',')[0].strip() if forwarded else request.remote_addr
    else:
        ip = request.remote_addr
    return ip or 'unknown'


# -------------------------------------------------------------------------
# Email validation
# -------------------------------------------------------------------------
# ReDoS-safe pattern: fixed-length character classes with no nested
# quantifiers. Each segment is bounded so catastrophic backtracking
# cannot occur on adversarial input (CodeQL py/polynomial-redos).
_EMAIL_LOCAL  = re.compile(r'^[A-Za-z0-9._%+\-]{1,64}$')
_EMAIL_DOMAIN = re.compile(r'^[A-Za-z0-9.\-]{1,253}$')
_EMAIL_TLD    = re.compile(r'^[A-Za-z]{2,}$')


def _valid_email(addr: str) -> bool:
    """Validate an email address without risk of ReDoS."""
    if not addr or not isinstance(addr, str):
        return False
    addr = addr.strip()
    if len(addr) > 254 or '@' not in addr:
        return False
    local, _, rest = addr.partition('@')
    if '.' not in rest:
        return False
    domain, _, tld = rest.rpartition('.')
    return bool(
        _EMAIL_LOCAL.match(local)
        and _EMAIL_DOMAIN.match(domain)
        and _EMAIL_TLD.match(tld)
    )


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
    path = app.config['SMTP_CONFIG_PATH']
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def _safe_smtp_config_summary(cfg: dict) -> dict:
    redacted = {k: v for k, v in cfg.items() if k != 'smtp_password'}
    redacted['smtp_password'] = '***redacted***'
    return redacted


def _sender_domain(smtp_config: dict) -> str:
    sender = smtp_config.get('smtp_sender_email', '')
    if '@' in sender:
        return sender.split('@', 1)[1]
    return 'localhost'


def _build_message(smtp_config, to_addr, subject, text_body, html_body, reply_to=None):
    sender_email = smtp_config.get('smtp_sender_email', '')
    domain = _sender_domain(smtp_config)

    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr(("iTransfer", sender_email))
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=domain)
    if reply_to:
        msg['Reply-To'] = reply_to
    msg['Auto-Submitted'] = 'auto-generated'
    msg['Precedence'] = 'bulk'
    msg['X-Mailer'] = 'iTransfer'
    msg['List-Unsubscribe'] = f'<mailto:{sender_email}?subject=unsubscribe>'
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    return msg


def send_email_with_smtp(msg, smtp_config) -> bool:
    server = None
    try:
        port = int(smtp_config['smtp_port'])
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port)
        else:
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
                pass


def get_backend_url() -> str:
    backend_url = os.environ.get('BACKEND_URL')
    if backend_url:
        if app.config['FORCE_HTTPS']:
            if backend_url.startswith('http://'):
                backend_url = 'https://' + backend_url[len('http://'):]
            elif not backend_url.startswith('https://'):
                backend_url = 'https://' + backend_url
        return backend_url
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
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #170017; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #400040, #693a67); border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: 1px; }}
            .content {{ padding: 30px; }}
            .message h2 {{ color: #693a67; margin: 0 0 15px; font-size: 20px; font-weight: 500; }}
            .files {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; white-space: pre-wrap; border: 1px solid rgba(0,0,0,0.05); margin: 20px 0; line-height: 1.8; font-size: 14px; }}
            .total {{ margin-top: 20px; padding: 12px 20px; background: linear-gradient(135deg, #400040, #693a67); color: #ffffff; border-radius: 8px; font-weight: 500; }}
            .footer {{ text-align: center; padding: 20px; color: #5a4e5a; font-size: 13px; border-top: 1px solid rgba(0,0,0,0.05); }}
            .download-btn {{ display: inline-block; margin: 20px 0; padding: 14px 28px; background: linear-gradient(135deg, #693a67, #7e547b); color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>iTransfer</h1></div>
            <div class="content">
                <div class="message"><h2>{title}</h2><p>{message}</p></div>
                {f'<a href="{download_link}" class="download-btn">Download files</a>' if download_link else ''}
                <div class="files">{file_summary}</div>
                <div class="total">{total_size}</div>
            </div>
            <div class="footer"><p>Sent via iTransfer</p></div>
        </div>
    </body>
    </html>
    """
    text = (
        f"{title}\n\n{message}\n\n"
        f"{'Download link: ' + download_link if download_link else ''}\n\n"
        f"File summary:\n{file_summary}\n\nTotal size: {total_size}\n"
    )
    return html, text


def _send_recipient_notification(recipient_email, file_id, files_summary, total_size, smtp_config, sender_email):
    try:
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            return False
        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        expiration_formatted = file_info.expires_at.astimezone(tz).strftime('%d/%m/%Y at %H:%M:%S')
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{file_id}"
        title = "You have received files"
        message = (
            f"{sender_email} sent you files. Click the button below "
            f"to access the download page.<br><br>"
            f"This link will expire on {expiration_formatted}"
        )
        html, text = create_email_template(title, message, files_summary, total_size, download_page_link)
        msg = _build_message(smtp_config, recipient_email,
                             f"{sender_email} sent you files",
                             text, html, reply_to=sender_email)
        return send_email_with_smtp(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare recipient notification")
        return False


def _send_sender_confirmation(sender_email, file_id, files_list, total_size, smtp_config, recipient_email):
    try:
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{file_id}"
        files_summary = "".join(f"- {f['name']} ({format_size(f['size'])})\n" for f in files_list)
        title = "Your files have been sent"
        message = (
            f"Your files have been sent to: {recipient_email}<br><br>"
            f"Download page: {download_page_link}"
        )
        html, text = create_email_template(title, message, files_summary, total_size)
        msg = _build_message(smtp_config, sender_email,
                             f"Transfer confirmation to {recipient_email}",
                             text, html)
        return send_email_with_smtp(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare sender confirmation")
        return False


def _send_download_notification(sender_email, file_id, smtp_config):
    try:
        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        download_time = datetime.now(tz).strftime('%d/%m/%Y at %H:%M:%S (%Z)')
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            return False
        files_list = file_info.get_files_list()
        if files_list:
            total = sum(f['size'] for f in files_list)
            files_summary = "".join(f"- {f['name']} ({format_size(f['size'])})\n" for f in files_list)
            total_formatted = format_size(total)
        else:
            stored_name = safe_stored_filename(file_info.filename)
            stored_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
            size = os.path.getsize(stored_path)
            files_summary = f"- {stored_name} ({format_size(size)})"
            total_formatted = format_size(size)
        title = "Your files have been downloaded"
        message = f"Your files were downloaded on {download_time}."
        html, text = create_email_template(title, message, files_summary, total_formatted)
        msg = _build_message(smtp_config, sender_email,
                             "Your files have been downloaded", text, html)
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

    if not _rate_limit(_client_key(), limit=RATE_LIMIT_LOGIN):
        return jsonify({'error': 'Too many requests'}), 429

    data = request.get_json(silent=True) or {}
    username = data.get('username', '')
    password = data.get('password', '')
    expected_user = app.config.get('ADMIN_USERNAME')
    expected_pass = app.config.get('ADMIN_PASSWORD')

    if not expected_user or not expected_pass:
        app.logger.error("Admin credentials not configured")
        return jsonify({'error': 'Server not configured'}), 503

    if username == expected_user and password == expected_pass:
        return jsonify({'token': issue_token(username)}), 200
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/upload', methods=['POST', 'OPTIONS'])
@require_auth
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200

    if not _rate_limit(_client_key()):
        return jsonify({'error': 'Too many requests'}), 429

    upload_root = app.config['UPLOAD_FOLDER']
    temp_dir = None
    zip_path = None
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')
        paths = request.form.getlist('paths[]')
        email = (request.form.get('email') or '').strip()
        sender_email = (request.form.get('sender_email') or '').strip()

        if not _valid_email(email):
            return jsonify({'error': 'Invalid recipient email address'}), 400
        if not _valid_email(sender_email):
            return jsonify({'error': 'Invalid sender email address'}), 400

        try:
            expiration_days = int(request.form.get('expiration_days', '7'))
        except ValueError:
            expiration_days = 7
        if expiration_days not in (3, 5, 7, 10):
            expiration_days = 7

        try:
            files_list = json.loads(request.form.get('files_list', '[]'))
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid files_list payload'}), 400
        if not files_list:
            return jsonify({'error': 'Empty files_list'}), 400

        total_size = sum(int(f.get('size', 0)) for f in files_list)

        file_id = str(uuid.uuid4())
        temp_dir = os.path.join(upload_root, 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)

        file_list = []
        for uploaded_file, raw_path in zip(files, paths):
            if not uploaded_file.filename:
                continue
            try:
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

        files_summary = "".join(f"- {f['name']} ({format_size(f['size'])})\n" for f in original_files)
        total_formatted = format_size(total_size)

        notification_errors = []
        try:
            smtp_config = _load_smtp_config()
            if not _send_recipient_notification(email, file_id, files_summary, total_formatted, smtp_config, sender_email):
                notification_errors.append("recipient")
            if not _send_sender_confirmation(sender_email, file_id, original_files, total_formatted, smtp_config, email):
                notification_errors.append("sender")
        except FileNotFoundError:
            app.logger.error("SMTP config missing")
            notification_errors.append("smtp not configured")
        except Exception:
            app.logger.exception("Notification dispatch failed")
            notification_errors.append("internal error")

        response = {'success': True, 'file_id': file_id, 'message': 'Upload OK'}
        if notification_errors:
            response['warning'] = "Notifications failed: " + ", ".join(notification_errors)
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
                pass
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
            'sender_email': record.sender_email,
        }), 200
    except UnsafePathError:
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
                pass
            except Exception:
                app.logger.exception("Failed to send download notification")

        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            stored_name,
            as_attachment=True,
            download_name=stored_name,
        )
    except UnsafePathError:
        return jsonify({'error': 'Not found'}), 404
    except Exception:
        app.logger.exception("Download failed")
        return jsonify({'error': 'Download failed'}), 500


# -------------------------------------------------------------------------
# Admin routes
# -------------------------------------------------------------------------
@app.route('/api/transfers', methods=['GET', 'OPTIONS'])
@require_auth
def list_transfers():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        records = FileUpload.query.order_by(FileUpload.created_at.desc()).all()
        result = []
        for r in records:
            files_list = r.get_files_list()
            total_size = sum(f.get('size', 0) for f in files_list)
            result.append({
                'id': r.id,
                'filename': r.filename,
                'sender_email': r.sender_email,
                'recipient_email': r.email,
                'created_at': r.created_at.isoformat() if r.created_at else None,
                'expires_at': r.expires_at.isoformat(),
                'downloaded': r.downloaded,
                'file_count': len(files_list),
                'total_size': total_size,
                'expired': datetime.utcnow() > r.expires_at,
            })
        return jsonify(result), 200
    except Exception:
        app.logger.exception("list_transfers failed")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/api/transfers/<file_id>', methods=['DELETE', 'OPTIONS'])
@require_auth
def delete_transfer(file_id):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        record = FileUpload.query.get(file_id)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        try:
            stored_name = safe_stored_filename(record.filename)
            file_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        except (UnsafePathError, OSError):
            app.logger.exception("Could not delete file for transfer %s", file_id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Deleted'}), 200
    except Exception:
        app.logger.exception("delete_transfer failed")
        return jsonify({'error': 'Internal error'}), 500


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

        if not _valid_email(data['smtpSenderEmail']):
            return jsonify({'error': 'Invalid sender email'}), 400

        smtp_config = {
            'smtp_server': data['smtpServer'],
            'smtp_port': data['smtpPort'],
            'smtp_user': data['smtpUser'],
            'smtp_password': data['smtpPassword'],
            'smtp_sender_email': data['smtpSenderEmail'],
        }
        app.logger.info("SMTP config updated")
        config_path = app.config['SMTP_CONFIG_PATH']
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as fh:
            json.dump(smtp_config, fh, indent=2)
        return jsonify({'message': 'SMTP config saved'}), 200
    except Exception:
        app.logger.exception("Failed to save SMTP config")
        return jsonify({'error': 'Could not save SMTP config'}), 500


@app.route('/api/get-smtp-settings', methods=['GET', 'OPTIONS'])
@require_auth
def get_smtp_settings():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        cfg = _load_smtp_config()
        return jsonify({
            'smtpServer': cfg.get('smtp_server', ''),
            'smtpPort': cfg.get('smtp_port', ''),
            'smtpUser': cfg.get('smtp_user', ''),
            'smtpSenderEmail': cfg.get('smtp_sender_email', ''),
            # password intentionally omitted
        }), 200
    except FileNotFoundError:
        return jsonify({}), 200
    except Exception:
        app.logger.exception("get_smtp_settings failed")
        return jsonify({'error': 'Internal error'}), 500


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
        msg = _build_message(
            smtp_config=smtp_config,
            to_addr=smtp_config['smtp_sender_email'],
            subject="SMTP configuration test",
            text_body="Test SMTP iTransfer.",
            html_body="<p>Test SMTP iTransfer.</p>",
        )
        if send_email_with_smtp(msg, smtp_config):
            return jsonify({'message': 'SMTP test OK'}), 200
        return jsonify({'error': 'SMTP test failed'}), 500
    except Exception:
        app.logger.exception("SMTP test error")
        return jsonify({'error': 'SMTP test failed'}), 500

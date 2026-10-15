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
import hmac
import json
import os
import re
import shutil
import smtplib
import threading
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
import pytz
from flask import Response, current_app, jsonify, request, send_from_directory, stream_with_context
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

from . import app, db, email_executor
from .auth import issue_token, require_auth, verify_bearer_header
from .deliverability import check_dkim, check_dmarc, check_spf
from .email_i18n import DEFAULT_LANGUAGE, normalize_language, t
from .models import FileUpload
from .paths import UnsafePathError, safe_join, safe_stored_filename
from .slug import generate_slug

_MAX_MESSAGE_LENGTH = 2000


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
_DKIM_SELECTOR = re.compile(r'^[A-Za-z0-9_\-]{1,63}$')
_TRANSFER_ID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
)


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


class _TransientSMTPError(Exception):
    """An SMTP failure worth retrying (network blip, 4xx temporary reject)."""


class _PermanentSMTPError(Exception):
    """An SMTP failure that will not succeed on retry (bad auth, 5xx, bad recipient)."""


_SMTP_TIMEOUT = 20  # seconds; a hung connection would otherwise block a worker thread forever


def send_email_with_smtp(msg, smtp_config) -> None:
    """Single delivery attempt. Raises _TransientSMTPError or
    _PermanentSMTPError on failure so callers can decide whether to retry."""
    server = None
    try:
        port = int(smtp_config['smtp_port'])
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], port, timeout=_SMTP_TIMEOUT)
        else:
            server = smtplib.SMTP(smtp_config['smtp_server'], port, timeout=_SMTP_TIMEOUT)
            server.starttls()
        server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
        server.send_message(msg)
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPRecipientsRefused) as e:
        # Fixed, safe category message -- never the raw exception text, which
        # can include server hostnames/ports or other internal detail. The
        # original exception is still chained (`from e`) for server-side logs.
        raise _PermanentSMTPError("SMTP authentication or recipient rejection") from e
    except smtplib.SMTPResponseException as e:
        # 4xx = temporary failure (greylisting, rate limit) -> retry.
        # 5xx = permanent failure (policy reject, bad address) -> don't.
        # The numeric SMTP code is a protocol-level status, not sensitive
        # detail (akin to an HTTP status code) -- safe to surface as-is.
        if 400 <= e.smtp_code < 500:
            raise _TransientSMTPError(f"SMTP temporary failure (code {e.smtp_code})") from e
        raise _PermanentSMTPError(f"SMTP permanent failure (code {e.smtp_code})") from e
    except (smtplib.SMTPServerDisconnected, ConnectionError, OSError) as e:
        # Pure connectivity failures (refused/unreachable/timed out) with no
        # SMTP response to classify -- always worth retrying. Note:
        # SMTPConnectError *is* a SMTPResponseException (it fires after a
        # non-220 banner) so it's already handled by the code-based branch
        # above, not here.
        raise _TransientSMTPError("SMTP connection failed") from e
    except Exception as e:
        # Unclassified failure: treat as permanent rather than retry-looping
        # on something that is more likely a bug than a transient blip.
        raise _PermanentSMTPError("unexpected SMTP failure") from e
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


def send_email_with_retry(msg, smtp_config, max_attempts: int = 3) -> tuple[bool, str | None]:
    """Send with bounded retries and exponential backoff, but only for
    transient failures. Returns (success, last_error_message_or_None)."""
    delay = 2
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            send_email_with_smtp(msg, smtp_config)
            return True, None
        except _PermanentSMTPError as e:
            # %s on e.__cause__ logs the original smtplib exception detail
            # (hostnames, full SMTP response text, etc.) server-side only;
            # the client/DB-facing message stays the sanitized str(e).
            app.logger.warning("Permanent SMTP failure, not retrying: %s (%s)", e, e.__cause__)
            return False, str(e)
        except _TransientSMTPError as e:
            last_error = str(e)
            app.logger.warning(
                "Transient SMTP failure (attempt %d/%d): %s (%s)", attempt, max_attempts, e, e.__cause__
            )
            if attempt < max_attempts:
                time.sleep(delay)
                delay *= 2
    return False, last_error


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


def create_email_template(title, message, file_summary, total_size, download_link=None,
                          sender_domain=None, lang=DEFAULT_LANGUAGE, user_message=None):
    footer_domain_line = (
        f'<p>{escape(t(lang, "footer_on_behalf", domain=sender_domain))}</p>' if sender_domain else ''
    )

    # Optional sender-supplied note. It is untrusted free text, so escape it
    # before it enters the HTML body and only then turn newlines into <br>.
    user_message_html = ''
    user_message_text = ''
    if user_message:
        safe_msg = str(escape(user_message)).replace('\n', '<br>')
        user_message_html = (
            f'<div class="user-message"><span class="user-message__label">'
            f'{escape(t(lang, "message_label"))}</span>{safe_msg}</div>'
        )
        user_message_text = f"{t(lang, 'message_label')}\n{user_message}\n\n"

    # Precomputed so the big template below contains only bare {name} fields:
    # on Python 3.10 an f-string replacement field cannot reuse the string's
    # own quote character, and the template is triple-double-quoted.
    footer_sent_via_html = escape(t(lang, 'footer_sent_via'))
    download_btn_html = ''
    if download_link:
        download_btn_html = (
            f'<a href="{download_link}" class="download-btn">'
            f'{escape(t(lang, "btn_download"))}</a>'
        )

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
            .user-message {{ background-color: #faf7fa; border-left: 3px solid #693a67; padding: 14px 18px; border-radius: 6px; margin: 20px 0; font-size: 14px; }}
            .user-message__label {{ display: block; font-weight: 600; color: #693a67; margin-bottom: 6px; font-size: 13px; }}
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
                {user_message_html}
                {download_btn_html}
                <div class="files">{file_summary}</div>
                <div class="total">{total_size}</div>
            </div>
            <div class="footer"><p>{footer_sent_via_html}</p>{footer_domain_line}</div>
        </div>
    </body>
    </html>
    """
    text = (
        f"{title}\n\n{message}\n\n"
        f"{user_message_text}"
        f"{t(lang, 'download_link_label') + ' ' + download_link if download_link else ''}\n\n"
        f"{t(lang, 'file_summary_label')}\n{file_summary}\n\n{t(lang, 'total_size_word')} {total_size}\n"
        f"{t(lang, 'footer_on_behalf', domain=sender_domain) if sender_domain else ''}\n"
    )
    return html, text


def _send_recipient_notification(recipient_email, file_id, files_summary, total_size, smtp_config,
                                 sender_email, lang=DEFAULT_LANGUAGE, user_message=None):
    """Build and send the recipient notification. Returns (success, error)."""
    try:
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            return False, "transfer not found"
        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        expiration_formatted = file_info.expires_at.astimezone(tz).strftime(
            f"%d/%m/%Y {t(lang, 'date_at')} %H:%M:%S"
        )
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{file_info.slug or file_id}"
        title = t(lang, 'recipient_title')
        message = (
            t(lang, 'recipient_body', sender=sender_email)
            + "<br><br>"
            + t(lang, 'expiry_line', date=expiration_formatted)
        )
        html, text = create_email_template(
            title, message, files_summary, total_size, download_page_link,
            sender_domain=_sender_domain(smtp_config), lang=lang, user_message=user_message,
        )
        msg = _build_message(smtp_config, recipient_email,
                             t(lang, 'recipient_subject', sender=sender_email),
                             text, html, reply_to=sender_email)
        return send_email_with_retry(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare recipient notification")
        return False, "internal error"


def _send_sender_confirmation(sender_email, file_id, files_list, total_size, smtp_config,
                              recipient_email, lang=DEFAULT_LANGUAGE):
    """Build and send the sender confirmation. Returns (success, error)."""
    try:
        file_info = FileUpload.query.get(file_id)
        link_id = (file_info.slug if file_info else None) or file_id
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3500').rstrip('/')
        download_page_link = f"{frontend_url}/download/{link_id}"
        files_summary = "".join(f"- {f['name']} ({format_size(f['size'])})\n" for f in files_list)
        title = t(lang, 'sender_title')
        message = (
            t(lang, 'sender_body', recipient=recipient_email)
            + "<br><br>"
            + t(lang, 'sender_download_page', link=download_page_link)
        )
        html, text = create_email_template(
            title, message, files_summary, total_size,
            sender_domain=_sender_domain(smtp_config), lang=lang,
        )
        msg = _build_message(smtp_config, sender_email,
                             t(lang, 'sender_subject', recipient=recipient_email),
                             text, html)
        return send_email_with_retry(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare sender confirmation")
        return False, "internal error"


def _send_download_notification(sender_email, file_id, smtp_config, lang=DEFAULT_LANGUAGE):
    """Build and send the download notification. Returns (success, error)."""
    try:
        tz = pytz.timezone(app.config.get('TIMEZONE', 'Europe/Paris'))
        download_time = datetime.now(tz).strftime(f"%d/%m/%Y {t(lang, 'date_at')} %H:%M:%S (%Z)")
        file_info = FileUpload.query.get(file_id)
        if not file_info:
            return False, "transfer not found"
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
        title = t(lang, 'download_title')
        message = t(lang, 'download_body', datetime=download_time)
        html, text = create_email_template(
            title, message, files_summary, total_formatted,
            sender_domain=_sender_domain(smtp_config), lang=lang,
        )
        msg = _build_message(smtp_config, sender_email,
                             t(lang, 'download_subject'), text, html)
        return send_email_with_retry(msg, smtp_config)
    except Exception:
        app.logger.exception("Failed to prepare download notification")
        return False, "internal error"


# -------------------------------------------------------------------------
# Background notification tasks
#
# Submitted to `email_executor` instead of being called inline from the
# request handlers, so a slow/unreachable SMTP server no longer delays the
# upload/download HTTP response. Each task runs outside the request
# context, so it must push its own app context to use app.logger/app.config
# and the DB session, and must call db.session.remove() at the end since
# the executor's worker threads are reused across many tasks (Flask-
# SQLAlchemy's scoped session is keyed by thread id).
# -------------------------------------------------------------------------
def _send_recipient_notification_task(file_id, recipient_email, files_summary, total_size, smtp_config,
                                      sender_email, lang=DEFAULT_LANGUAGE, user_message=None):
    with app.app_context():
        try:
            success, error = _send_recipient_notification(
                recipient_email, file_id, files_summary, total_size, smtp_config,
                sender_email, lang, user_message,
            )
            record = FileUpload.query.get(file_id)
            if record:
                record.notification_status_recipient = 'sent' if success else 'failed'
                record.notification_error_recipient = error
                db.session.commit()
        except Exception:
            app.logger.exception("Recipient notification task failed for %s", file_id)
        finally:
            db.session.remove()


def _send_sender_confirmation_task(file_id, sender_email, files_list, total_size, smtp_config,
                                   recipient_email, lang=DEFAULT_LANGUAGE):
    with app.app_context():
        try:
            success, error = _send_sender_confirmation(
                sender_email, file_id, files_list, total_size, smtp_config, recipient_email, lang
            )
            record = FileUpload.query.get(file_id)
            if record:
                record.notification_status_sender = 'sent' if success else 'failed'
                record.notification_error_sender = error
                db.session.commit()
        except Exception:
            app.logger.exception("Sender confirmation task failed for %s", file_id)
        finally:
            db.session.remove()


def _send_download_notification_task(file_id, sender_email, smtp_config, lang=DEFAULT_LANGUAGE):
    with app.app_context():
        try:
            success, error = _send_download_notification(sender_email, file_id, smtp_config, lang)
            record = FileUpload.query.get(file_id)
            if record:
                record.notification_status_download = 'sent' if success else 'failed'
                record.notification_error_download = error
                db.session.commit()
        except Exception:
            app.logger.exception("Download notification task failed for %s", file_id)
        finally:
            db.session.remove()


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


def _tus_hook_json(body: dict):
    """Hook responses must always be HTTP 200 with a JSON body -- tusd treats
    any non-2XX from this endpoint as an internal failure (retried, then a
    500 to the uploading client) rather than as a deliberate rejection.
    Rejection is instead signalled inside the body via RejectUpload /
    HTTPResponse, per tusd's hook contract."""
    return jsonify(body), 200


def _tus_reject(status: int, message: str):
    return _tus_hook_json({
        'RejectUpload': True,
        'HTTPResponse': {
            'StatusCode': status,
            'Body': json.dumps({'error': message}),
            'Header': {'Content-Type': 'application/json'},
        },
    })


def _tus_hook_pre_create(event: dict):
    headers = (event.get('HTTPRequest') or {}).get('Header') or {}
    auth_values = headers.get('Authorization') or []
    if not verify_bearer_header(auth_values[0] if auth_values else ''):
        return _tus_reject(401, 'Authentication required')

    upload = event.get('Upload') or {}
    size = upload.get('Size')
    if size is not None and size > app.config['MAX_CONTENT_LENGTH']:
        return _tus_reject(413, 'File too large')

    metadata = upload.get('MetaData') or {}
    if not metadata.get('transfer_id') or not metadata.get('relative_path'):
        return _tus_reject(400, 'Missing transfer metadata')

    return _tus_hook_json({})


def _tus_hook_post_finish(event: dict) -> None:
    """Move the file tusd just finished receiving out of its own transit
    storage and into this transfer's temp directory, using the metadata the
    frontend attached at creation time to know where it belongs. Runs after
    tusd has already answered the client, so nothing here can affect the
    response -- failures are only logged."""
    upload = event.get('Upload') or {}
    metadata = upload.get('MetaData') or {}
    transfer_id = metadata.get('transfer_id') or ''
    relative_path = metadata.get('relative_path') or ''
    storage_path = (upload.get('Storage') or {}).get('Path')

    if not _TRANSFER_ID_RE.match(transfer_id) or not relative_path or not storage_path:
        app.logger.warning("post-finish hook missing or invalid metadata")
        return

    # Defense in depth: the hook secret already authenticates the caller as
    # tusd, but a filesystem path from a webhook payload is still never
    # trusted blindly -- confirm it actually lives inside tusd's own storage
    # before moving anything.
    tusd_root = os.path.realpath(app.config['TUSD_DATA_DIR'])
    source = os.path.realpath(storage_path)
    if source != tusd_root and not source.startswith(tusd_root + os.sep):
        app.logger.warning("post-finish hook reported a path outside tusd storage")
        return
    if not os.path.isfile(source):
        app.logger.warning("post-finish hook reported a missing file: %s", source)
        return

    try:
        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', transfer_id)
        target_path = safe_join(target_dir, relative_path)
    except UnsafePathError:
        app.logger.warning("post-finish hook reported an unsafe relative path")
        return

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.move(source, target_path)
    info_path = source + '.info'
    if os.path.exists(info_path):
        try:
            os.remove(info_path)
        except OSError:
            pass


@app.route('/api/tus-hooks', methods=['POST'])
def tus_hooks():
    """Webhook endpoint tusd calls for pre-create/post-finish/post-terminate
    (see -hooks-http / -hooks-enabled-events in docker-compose.yml). Guarded
    by a shared secret, not JWT, since this is tusd calling us, not the
    browser -- the pre-create hook below validates the *uploading user's*
    JWT separately, forwarded inside the hook payload itself."""
    secret = request.args.get('secret', '')
    if not hmac.compare_digest(secret, app.config['TUS_HOOK_SECRET']):
        app.logger.warning("Rejected /api/tus-hooks call with invalid secret")
        return jsonify({'error': 'Forbidden'}), 403

    payload = request.get_json(silent=True) or {}
    hook_type = payload.get('Type', '')
    event = payload.get('Event') or {}

    if hook_type == 'pre-create':
        return _tus_hook_pre_create(event)
    if hook_type == 'post-finish':
        _tus_hook_post_finish(event)
    # post-terminate: tusd's own filestore already deletes the partial
    # upload's data when the client aborts/terminates it -- nothing of ours
    # exists yet at that point (post-finish is what creates it), so there is
    # nothing to clean up here.
    return _tus_hook_json({})


@app.route('/api/transfers/finalize', methods=['POST', 'OPTIONS'])
@require_auth
def finalize_transfer():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200

    if not _rate_limit(_client_key()):
        return jsonify({'error': 'Too many requests'}), 429

    data = request.get_json(silent=True) or {}
    transfer_id = (data.get('transfer_id') or '').strip()
    if not _TRANSFER_ID_RE.match(transfer_id):
        return jsonify({'error': 'Invalid transfer id'}), 400

    upload_root = app.config['UPLOAD_FOLDER']
    temp_dir = os.path.join(upload_root, 'temp', transfer_id)
    zip_path = None
    try:
        email = (data.get('email') or '').strip()
        sender_email = (data.get('sender_email') or '').strip()
        language = normalize_language(data.get('language'))
        user_message = (data.get('message') or '').strip()[:_MAX_MESSAGE_LENGTH] or None
        transfer_password = (data.get('password') or '').strip() or None
        password_hash = generate_password_hash(transfer_password) if transfer_password else None

        if not _valid_email(email):
            return jsonify({'error': 'Invalid recipient email address'}), 400
        if not _valid_email(sender_email):
            return jsonify({'error': 'Invalid sender email address'}), 400

        try:
            expiration_days = int(data.get('expiration_days', 7))
        except (TypeError, ValueError):
            expiration_days = 7
        if expiration_days not in (3, 5, 7, 10):
            expiration_days = 7

        download_limit = None
        try:
            parsed_limit = int(data.get('download_limit') or 0)
            if parsed_limit > 0:
                download_limit = parsed_limit
        except (TypeError, ValueError):
            pass

        files_list = data.get('files_list') or []
        if not files_list:
            return jsonify({'error': 'Empty files_list'}), 400

        # Each file's post-finish hook runs independently, so by the time the
        # client calls this endpoint one of them may not have landed in
        # temp_dir yet -- retry briefly instead of failing the whole transfer
        # on that race.
        file_entries = None
        for attempt in range(5):
            try:
                entries = []
                for f in files_list:
                    relative = f.get('name')
                    stored_path = safe_join(temp_dir, relative)
                    entries.append({
                        'relative': relative,
                        'size': os.path.getsize(stored_path),
                        'abs': stored_path,
                    })
                file_entries = entries
                break
            except OSError:
                if attempt < 4:
                    time.sleep(0.5 * (attempt + 1))

        if file_entries is None:
            return jsonify({'error': 'Uploaded files not found yet, please retry'}), 409

        file_id = transfer_id
        needs_zip = len(file_entries) > 1 or any('/' in f['relative'] for f in file_entries)

        if needs_zip:
            date_str = datetime.utcnow().strftime("%y%m%d%H%M%S")
            final_filename = f"iTransfer_{date_str}_{file_id[:8]}.zip"
            zip_path = safe_join(upload_root, final_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for entry in file_entries:
                    zf.write(entry['abs'], entry['relative'])
            final_path = zip_path
        else:
            only = file_entries[0]
            final_filename = safe_stored_filename(only['relative'])
            final_path = safe_join(upload_root, final_filename)
            shutil.move(only['abs'], final_path)

        # Stream the hash in fixed-size chunks. fh.read() with no argument
        # pulls the entire file into memory at once -- on a multi-GB transfer
        # that alone can exhaust the worker's RAM and get it OOM-killed
        # mid-request, surfacing to the client as a dropped connection.
        hasher = hashlib.sha256()
        with open(final_path, 'rb') as fh:
            for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b''):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()

        original_files = [{'name': f.get('name'), 'size': int(f.get('size', 0))} for f in files_list]
        total_size = sum(f['size'] for f in original_files)

        # Human-readable public link. Collisions are astronomically unlikely
        # (4 words drawn from two ~90-word lists) but checked anyway since
        # the cost of checking is trivial next to the cost of a collision.
        slug = generate_slug()
        while FileUpload.query.filter_by(slug=slug).first() is not None:
            slug = generate_slug()

        record = FileUpload(
            id=file_id,
            filename=final_filename,
            email=email,
            sender_email=sender_email,
            encrypted_data=file_hash,
            downloaded=False,
            expires_at=datetime.utcnow() + timedelta(days=expiration_days),
            message=user_message,
            language=language,
            slug=slug,
            password_hash=password_hash,
            download_limit=download_limit,
            download_count=0,
        )
        record.set_files_list(original_files)
        db.session.add(record)
        db.session.commit()

        files_summary = "".join(f"- {f['name']} ({format_size(f['size'])})\n" for f in original_files)
        total_formatted = format_size(total_size)

        try:
            smtp_config = _load_smtp_config()
            record.notification_status_recipient = 'pending'
            record.notification_status_sender = 'pending'
            db.session.commit()
            email_executor.submit(
                _send_recipient_notification_task, file_id, email, files_summary,
                total_formatted, smtp_config, sender_email, language, user_message,
            )
            email_executor.submit(
                _send_sender_confirmation_task, file_id, sender_email, original_files,
                total_formatted, smtp_config, email, language,
            )
        except FileNotFoundError:
            app.logger.error("SMTP config missing; notifications not dispatched for %s", file_id)
            record.notification_status_recipient = 'failed'
            record.notification_error_recipient = 'SMTP not configured'
            record.notification_status_sender = 'failed'
            record.notification_error_sender = 'SMTP not configured'
            db.session.commit()
        except Exception:
            app.logger.exception("Notification dispatch failed for %s", file_id)

        return jsonify({'success': True, 'file_id': file_id, 'slug': slug}), 200

    except UnsafePathError:
        app.logger.warning("Unsafe path in finalize request")
        return jsonify({'error': 'Invalid file path'}), 400
    except Exception:
        app.logger.exception("Transfer finalize failed")
        if zip_path and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass
        return jsonify({'error': 'Finalize failed'}), 500
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def _find_transfer(identifier):
    """Look up a transfer by its public slug first, falling back to the raw
    internal id -- covers links sent before the slug column existed."""
    record = FileUpload.query.filter_by(slug=identifier).first()
    if record:
        return record
    return FileUpload.query.get(identifier)


def _transfer_expired(record) -> bool:
    if datetime.utcnow() > record.expires_at:
        return True
    if record.download_limit is not None and (record.download_count or 0) >= record.download_limit:
        return True
    return False


def _transfer_payload(record) -> dict:
    """Shared response body for the detail and unlock endpoints. Raises
    FileNotFoundError if the stored file is missing so callers can turn that
    into the existing 404 message without duplicating the check."""
    stored_name = safe_stored_filename(record.filename)
    file_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    files_list = record.get_files_list()
    if not files_list:
        files_list = [{'name': stored_name, 'size': os.path.getsize(file_path)}]

    return {
        'files': files_list,
        'expires_at': record.expires_at.isoformat(),
        'sender_email': record.sender_email,
        'message': record.message,
    }


@app.route('/transfer/<identifier>', methods=['GET'])
def get_transfer_details(identifier):
    try:
        record = _find_transfer(identifier)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        if _transfer_expired(record):
            return jsonify({'error': 'Link expired'}), 410

        # Never expose the file list or message before the password check --
        # the frontend shows a password prompt and calls /unlock instead.
        if record.password_hash:
            return jsonify({'password_required': True}), 200

        return jsonify(_transfer_payload(record)), 200
    except FileNotFoundError:
        return jsonify({'error': 'File missing on server'}), 404
    except UnsafePathError:
        return jsonify({'error': 'Not found'}), 404
    except Exception:
        app.logger.exception("transfer details failed")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/transfer/<identifier>/unlock', methods=['POST', 'OPTIONS'])
def unlock_transfer(identifier):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    if not _rate_limit(_client_key()):
        return jsonify({'error': 'Too many requests'}), 429
    try:
        record = _find_transfer(identifier)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        if _transfer_expired(record):
            return jsonify({'error': 'Link expired'}), 410

        if record.password_hash:
            password = (request.get_json(silent=True) or {}).get('password') or ''
            if not check_password_hash(record.password_hash, password):
                return jsonify({'error': 'Incorrect password'}), 403

        return jsonify(_transfer_payload(record)), 200
    except FileNotFoundError:
        return jsonify({'error': 'File missing on server'}), 404
    except UnsafePathError:
        return jsonify({'error': 'Not found'}), 404
    except Exception:
        app.logger.exception("transfer unlock failed")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/download/<identifier>', methods=['GET'])
def download_file(identifier):
    try:
        record = _find_transfer(identifier)
        if not record:
            return jsonify({'error': 'Not found'}), 404
        if _transfer_expired(record):
            return jsonify({'error': 'Link expired'}), 410

        if record.password_hash:
            password = request.headers.get('X-Transfer-Password', '')
            if not check_password_hash(record.password_hash, password):
                return jsonify({'error': 'Incorrect password'}), 403

        stored_name = safe_stored_filename(record.filename)
        file_path = safe_join(app.config['UPLOAD_FOLDER'], stored_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File missing on server'}), 404

        record.download_count = (record.download_count or 0) + 1

        if not record.downloaded:
            record.downloaded = True
            try:
                smtp_config = _load_smtp_config()
                record.notification_status_download = 'pending'
                db.session.commit()
                email_executor.submit(
                    _send_download_notification_task, record.id, record.sender_email, smtp_config,
                    normalize_language(record.language),
                )
            except FileNotFoundError:
                app.logger.error("SMTP config missing; download notification not dispatched for %s", record.id)
                record.notification_status_download = 'failed'
                record.notification_error_download = 'SMTP not configured'
                db.session.commit()
            except Exception:
                app.logger.exception("Failed to dispatch download notification for %s", record.id)
                db.session.commit()
        else:
            db.session.commit()

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
                'notifications': {
                    'recipient': {'status': r.notification_status_recipient, 'error': r.notification_error_recipient},
                    'sender': {'status': r.notification_status_sender, 'error': r.notification_error_sender},
                    'download': {'status': r.notification_status_download, 'error': r.notification_error_download},
                },
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
        data = request.get_json(silent=True) or {}
        lang = normalize_language(data.get('language'))
        test_body = t(lang, 'smtp_test_body')
        msg = _build_message(
            smtp_config=smtp_config,
            to_addr=smtp_config['smtp_sender_email'],
            subject=t(lang, 'smtp_test_subject'),
            text_body=test_body,
            html_body=f"<p>{escape(test_body)}</p>",
        )
        success, error = send_email_with_retry(msg, smtp_config)
        if success:
            return jsonify({'message': 'SMTP test OK'}), 200
        return jsonify({'error': 'SMTP test failed'}), 500
    except Exception:
        app.logger.exception("SMTP test error")
        return jsonify({'error': 'SMTP test failed'}), 500


@app.route('/api/check-deliverability', methods=['POST', 'OPTIONS'])
@require_auth
def check_deliverability():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'ok'}), 200
    try:
        try:
            smtp_config = _load_smtp_config()
        except FileNotFoundError:
            return jsonify({'error': 'SMTP not configured yet'}), 404

        domain = _sender_domain(smtp_config)
        data = request.get_json(silent=True) or {}
        selector = (data.get('dkim_selector') or '').strip()
        if selector and not _DKIM_SELECTOR.match(selector):
            return jsonify({'error': 'Invalid DKIM selector format'}), 400

        result = {
            'domain': domain,
            'spf': check_spf(domain),
            'dmarc': check_dmarc(domain),
        }
        if selector:
            result['dkim'] = check_dkim(domain, selector)
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Deliverability check failed")
        return jsonify({'error': 'Deliverability check failed'}), 500

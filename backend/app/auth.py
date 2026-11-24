"""JWT authentication for protected endpoints."""
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, jsonify, request


def issue_token(subject: str) -> str:
    payload = {
        'sub': subject,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS']),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def _decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])


def verify_bearer_header(header: str) -> bool:
    """Validate a raw "Authorization: Bearer <token>" header value outside of
    a normal Flask request/view -- e.g. from a webhook payload that merely
    forwards the original request's headers. Returns True iff valid.

    Logs the specific rejection reason (never the token itself) so a 401
    here can be diagnosed from the logs instead of guessed at -- this
    endpoint has no browser-visible response body to inspect."""
    if not header:
        current_app.logger.warning("Bearer token rejected: no Authorization header present")
        return False
    if not header.startswith('Bearer '):
        current_app.logger.warning(
            "Bearer token rejected: Authorization header present but not a Bearer token (starts with: %r)",
            header[:15],
        )
        return False
    token = header[len('Bearer '):].strip()
    try:
        _decode_token(token)
        return True
    except jwt.ExpiredSignatureError:
        current_app.logger.warning("Bearer token rejected: expired")
        return False
    except jwt.InvalidTokenError as exc:
        current_app.logger.warning("Bearer token rejected: invalid (%s: %s)", type(exc).__name__, exc)
        return False


def require_auth(view):
    """Decorator that rejects requests without a valid bearer token."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            return view(*args, **kwargs)
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        token = header[len('Bearer '):].strip()
        try:
            _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return view(*args, **kwargs)
    return wrapper

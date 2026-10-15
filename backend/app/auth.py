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
    forwards the original request's headers. Returns True iff valid."""
    if not header or not header.startswith('Bearer '):
        return False
    token = header[len('Bearer '):].strip()
    try:
        _decode_token(token)
        return True
    except jwt.InvalidTokenError:
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

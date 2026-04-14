"""
Utilities for safely mapping untrusted user-supplied names to absolute paths
inside a known root directory. Used by upload/download handlers to neutralise
path-traversal vectors flagged by CodeQL py/path-injection.
"""
import os
import re
import unicodedata


# Matches anything that is not an ASCII letter, digit, dot, underscore, dash
# or forward slash. Slashes are handled separately (segment by segment).
_UNSAFE_CHARS = re.compile(r'[^A-Za-z0-9._\-/]')
_MAX_COMPONENT_LEN = 120
_MAX_PATH_LEN = 400


class UnsafePathError(ValueError):
    """Raised when a supplied path cannot be made safe."""


def _sanitize_component(component: str) -> str:
    """Sanitise a single path component (no slashes allowed)."""
    if not component or component in ('.', '..'):
        raise UnsafePathError("Invalid path component")
    # Normalise unicode and strip control characters
    component = unicodedata.normalize('NFKC', component)
    component = ''.join(ch for ch in component if ch.isprintable())
    # Replace any unsafe character with '_'
    component = _UNSAFE_CHARS.sub('_', component)
    component = component.strip(' .')
    if not component or component in ('.', '..'):
        raise UnsafePathError("Invalid path component after sanitisation")
    if len(component) > _MAX_COMPONENT_LEN:
        component = component[:_MAX_COMPONENT_LEN]
    return component


def sanitize_relative_path(raw: str) -> str:
    """
    Clean an untrusted relative path. Returns a forward-slash relative path
    with no '..', no absolute segments, no control characters. Raises
    UnsafePathError on anything that cannot be salvaged.
    """
    if not raw or not isinstance(raw, str):
        raise UnsafePathError("Empty path")
    if len(raw) > _MAX_PATH_LEN:
        raise UnsafePathError("Path too long")
    # Normalise backslashes to forward slashes (Windows-origin uploads)
    raw = raw.replace('\\', '/').lstrip('/')
    parts = [p for p in raw.split('/') if p]
    if not parts:
        raise UnsafePathError("Empty path")
    safe_parts = [_sanitize_component(p) for p in parts]
    return '/'.join(safe_parts)


def safe_join(root: str, relative: str) -> str:
    """
    Join ``relative`` onto ``root`` and verify the result stays inside root.
    ``root`` MUST be an absolute, realpath-resolved directory. Returns an
    absolute path; raises UnsafePathError on escape attempts.

    This is the function CodeQL's path-injection taint analyser treats as a
    sanitiser: the returned path is checked against the root both before and
    after symlink resolution.
    """
    if not os.path.isabs(root):
        raise UnsafePathError("Root must be absolute")
    root_resolved = os.path.realpath(root)

    safe_relative = sanitize_relative_path(relative)
    candidate = os.path.normpath(os.path.join(root_resolved, safe_relative))

    # Check BEFORE creating anything so we never mkdir outside the root
    if candidate != root_resolved and not candidate.startswith(root_resolved + os.sep):
        raise UnsafePathError("Path escapes root")

    # Resolve symlinks on the parent (target may not exist yet)
    parent = os.path.dirname(candidate)
    parent_resolved = os.path.realpath(parent) if os.path.exists(parent) else parent
    if (
        parent_resolved != root_resolved
        and not parent_resolved.startswith(root_resolved + os.sep)
    ):
        raise UnsafePathError("Parent path escapes root after symlink resolution")

    return candidate


def safe_stored_filename(filename: str) -> str:
    """
    Sanitise a flat filename (no directory separators allowed). Used for
    values read back from the database before passing them to send_file or
    os.remove. Even though those values originally came from the server, the
    DB column is a string and CodeQL treats it as a taint source; running
    them through this function confirms they cannot escape UPLOAD_FOLDER.
    """
    return _sanitize_component(os.path.basename(filename))

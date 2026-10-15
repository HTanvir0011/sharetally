"""Authentication, sessions, CSRF and login throttling for the prototype."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time

MAX_FAILURES = 5
FAILURE_WINDOW_S = 15 * 60

ROLES = {
    "reviewer": "AC Land office reviewer",
    "clerk": "Sub-Registry clerk",
    "auditor": "Auditor (read-only)",
}


def hash_password(password: str, iterations: int, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), iterations)
    return salt, digest.hex()


def verify_password(password: str, salt: str, expected_hash: str, iterations: int) -> bool:
    _, digest = hash_password(password, iterations, salt)
    return hmac.compare_digest(digest, expected_hash)


def ensure_users(conn: sqlite3.Connection, users: tuple, iterations: int) -> None:
    for username, role, display, password in users:
        if conn.execute("SELECT 1 FROM app_user WHERE username = ?", (username,)).fetchone():
            continue
        salt, digest = hash_password(password, iterations)
        conn.execute("INSERT INTO app_user VALUES (?, ?, ?, ?, ?, ?)", (username, role, display, salt, digest, iterations))
    conn.commit()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def throttled(conn: sqlite3.Connection, keys: list[str]) -> bool:
    since = time.time() - FAILURE_WINDOW_S
    for key in keys:
        n = conn.execute("SELECT COUNT(*) FROM login_attempt WHERE key = ? AND ts > ?", (key, since)).fetchone()[0]
        if n >= MAX_FAILURES:
            return True
    return False


def record_failure(conn: sqlite3.Connection, keys: list[str]) -> None:
    now = time.time()
    conn.executemany("INSERT INTO login_attempt VALUES (?, ?)", [(k, now) for k in keys])
    conn.execute("DELETE FROM login_attempt WHERE ts < ?", (now - FAILURE_WINDOW_S,))
    conn.commit()


def authenticate(conn: sqlite3.Connection, username: str, password: str) -> sqlite3.Row | None:
    user = conn.execute("SELECT * FROM app_user WHERE username = ?", (username,)).fetchone()
    if user is None:
        # Spend comparable time so response timing does not reveal valid usernames.
        hash_password(password, 100_000, "00" * 16)
        return None
    if verify_password(password, user["pw_salt"], user["pw_hash"], user["pw_iterations"]):
        return user
    return None


def create_session(conn: sqlite3.Connection, username: str, hours: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    now = time.time()
    conn.execute("DELETE FROM session WHERE expires_at < ?", (now,))
    conn.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?)", (_token_hash(token), username, csrf, now, now + hours * 3600))
    conn.commit()
    return token, csrf


def load_session(conn: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    if not token or len(token) > 200:
        return None
    return conn.execute(
        """SELECT s.csrf, s.expires_at, u.username, u.role, u.display_name
           FROM session s JOIN app_user u ON u.username = s.username
           WHERE s.token_hash = ? AND s.expires_at > ?""", (_token_hash(token), time.time())).fetchone()


def destroy_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM session WHERE token_hash = ?", (_token_hash(token),))
        conn.commit()


def csrf_ok(expected: str | None, supplied: str | None) -> bool:
    return bool(expected and supplied) and hmac.compare_digest(expected, supplied)

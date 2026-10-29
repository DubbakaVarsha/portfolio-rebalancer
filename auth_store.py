"""Small local authentication and per-user plan store for the portfolio demo."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUTH_DB = Path(os.environ.get("AUTH_DB", ROOT / "data" / "user_store.sqlite"))
PASSWORD_ITERATIONS = 600_000
SESSION_SECONDS = 7 * 24 * 60 * 60
_DUMMY_SALT = bytes.fromhex("d45c7c9e78b8775df3abe391308729cc")
_DUMMY_HASH = hashlib.pbkdf2_hmac("sha256", b"invalid-account-password", _DUMMY_SALT, PASSWORD_ITERATIONS)


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(AUTH_DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def initialize() -> None:
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            csrf_token TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON sessions(expires_at);
        CREATE TABLE IF NOT EXISTS plans (
            user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            plan_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """)


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if (len(email) > 254 or email.count("@") != 1 or any(ch.isspace() for ch in email)):
        raise ValueError("Enter a valid email address.")
    local, domain = email.split("@")
    if not local or len(local) > 64 or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Enter a valid email address.")
    return email


def hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    encoded = password.encode("utf-8")
    if not 12 <= len(password) <= 128 or len(encoded) > 1024:
        raise ValueError("Use a passphrase between 12 and 128 characters.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", encoded, salt, PASSWORD_ITERATIONS)
    return salt, digest


def create_user(email: str, display_name: str, password: str) -> dict:
    email = normalize_email(email)
    display_name = display_name.strip()[:60] or email.split("@", 1)[0]
    salt, digest = hash_password(password)
    user = {"user_id": str(uuid.uuid4()), "email": email, "display_name": display_name}
    try:
        with connect() as con:
            con.execute("INSERT INTO users(user_id,email,display_name,password_salt,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                        (user["user_id"], email, display_name, salt, digest, int(time.time())))
    except sqlite3.IntegrityError as exc:
        raise ValueError("Could not create the account. Try signing in or use another email.") from exc
    return user


def authenticate(email: str, password: str) -> dict | None:
    try:
        email = normalize_email(email)
    except ValueError:
        email = "invalid@example.invalid"
    with connect() as con:
        row = con.execute("SELECT user_id,email,display_name,password_salt,password_hash FROM users WHERE email=?", (email,)).fetchone()
    salt = bytes(row["password_salt"]) if row else _DUMMY_SALT
    expected = bytes(row["password_hash"]) if row else _DUMMY_HASH
    try:
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8")[:1024], salt, PASSWORD_ITERATIONS)
    except (AttributeError, UnicodeEncodeError):
        actual = hashlib.pbkdf2_hmac("sha256", b"invalid", salt, PASSWORD_ITERATIONS)
    if not row or not hmac.compare_digest(actual, expected):
        return None
    return {"user_id": row["user_id"], "email": row["email"], "display_name": row["display_name"]}


def create_session(user_id: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    now = int(time.time())
    with connect() as con:
        con.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
        con.execute("INSERT INTO sessions(session_hash,user_id,csrf_token,expires_at,created_at) VALUES(?,?,?,?,?)",
                    (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf, now + SESSION_SECONDS, now))
    return token, csrf


def get_session(token: str | None) -> dict | None:
    if not token or len(token) > 128:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect() as con:
        row = con.execute("""SELECT s.session_hash,s.csrf_token,s.expires_at,u.user_id,u.email,u.display_name
            FROM sessions s JOIN users u USING(user_id) WHERE s.session_hash=? AND s.expires_at>?""",
                          (token_hash, int(time.time()))).fetchone()
    return dict(row) if row else None


def revoke_session(token: str | None) -> None:
    if not token or len(token) > 128:
        return
    with connect() as con:
        con.execute("DELETE FROM sessions WHERE session_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))


def read_plan(user_id: str) -> tuple[dict | None, int | None]:
    with connect() as con:
        row = con.execute("SELECT plan_json,updated_at FROM plans WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return None, None
    try:
        return json.loads(row["plan_json"]), row["updated_at"]
    except (TypeError, ValueError):
        return None, None


def save_plan(user_id: str, plan: dict) -> int:
    serialized = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 16_384:
        raise ValueError("Plan is too large to save.")
    now = int(time.time())
    with connect() as con:
        con.execute("""INSERT INTO plans(user_id,plan_json,updated_at) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET plan_json=excluded.plan_json,updated_at=excluded.updated_at""",
                    (user_id, serialized, now))
    return now

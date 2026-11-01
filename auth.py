import hashlib
import hmac
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "users.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            salt BLOB NOT NULL,
            pw_hash BLOB NOT NULL
        )
    """)
    return conn


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


def create_user(name: str, email: str, password: str):
    email = email.strip().lower()
    name = name.strip()

    if not name:
        return False, "Enter your name."
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    salt = os.urandom(16)
    try:
        with closing(_conn()) as conn, conn:
            conn.execute(
                "INSERT INTO users (email, name, salt, pw_hash) "
                "VALUES (?, ?, ?, ?)",
                (email, name, salt, _hash(password, salt)),
            )
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

    return True, None


def verify_user(email: str, password: str):
    email = email.strip().lower()
    with closing(_conn()) as conn:
        row = conn.execute(
            "SELECT name, salt, pw_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not row:
        return None

    name, salt, pw_hash = row
    if hmac.compare_digest(_hash(password, salt), pw_hash):
        return {"name": name, "email": email}
    return None
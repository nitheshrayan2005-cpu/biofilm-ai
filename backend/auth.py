"""
BiofilmAI Backend — Doctor authentication.

Doctor accounts live in `doctors.json` (passwords stored as PBKDF2 hashes,
never in plain text). Signing in returns a signed token that the frontend
sends as `Authorization: Bearer <token>` on every protected request.

Manage accounts from the command line:
    python auth.py add <username> "<Display name>"     # prompts for password
    python auth.py remove <username>
    python auth.py list
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import Header, HTTPException

BASE_DIR = Path(__file__).resolve().parent
DOCTORS_FILE = BASE_DIR / "doctors.json"
SECRET_FILE = BASE_DIR / ".auth_secret"

TOKEN_TTL_SECONDS = int(os.getenv("BIOFILM_SESSION_HOURS", "12")) * 3600
PBKDF2_ITERATIONS = 200_000

# Doctor sign-in is required by default. Set BIOFILM_REQUIRE_LOGIN=false (and
# LOGIN_REQUIRED = false in lib/auth.ts) to run every request as GUEST_DOCTOR.
REQUIRE_LOGIN = os.getenv("BIOFILM_REQUIRE_LOGIN", "true").lower() == "true"
GUEST_DOCTOR = {"username": "guest", "name": "Researcher"}

# Lock an account for a while after repeated wrong passwords.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 5 * 60


# ── Secret key ───────────────────────────────────────────────────────────

def _load_secret() -> bytes:
    """Use BIOFILM_SECRET_KEY if set, otherwise a key persisted on disk."""
    from_env = os.getenv("BIOFILM_SECRET_KEY", "").strip()
    if from_env:
        return from_env.encode()
    if SECRET_FILE.is_file():
        return SECRET_FILE.read_text().strip().encode()
    key = secrets.token_hex(32)
    SECRET_FILE.write_text(key)
    return key.encode()


_SECRET = _load_secret()


# ── Password hashing ─────────────────────────────────────────────────────

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return salt, digest.hex()


def _load_doctors() -> dict:
    if not DOCTORS_FILE.is_file():
        return {}
    return json.loads(DOCTORS_FILE.read_text(encoding="utf-8"))


def _save_doctors(doctors: dict) -> None:
    DOCTORS_FILE.write_text(json.dumps(doctors, indent=2), encoding="utf-8")


# ── Login ────────────────────────────────────────────────────────────────

_failed: dict[str, tuple[int, float]] = {}
_failed_lock = threading.Lock()


def authenticate(username: str, password: str) -> dict:
    """Return the doctor's public profile, or raise 401/429."""
    username = (username or "").strip().lower()

    with _failed_lock:
        count, since = _failed.get(username, (0, 0.0))
        if count >= MAX_FAILED_ATTEMPTS and time.time() - since < LOCKOUT_SECONDS:
            raise HTTPException(
                status_code=429,
                detail="Too many failed attempts. Try again in a few minutes.",
            )

    doctor = _load_doctors().get(username)
    ok = False
    if doctor:
        _, digest = hash_password(password or "", doctor["salt"])
        ok = hmac.compare_digest(digest, doctor["hash"])

    with _failed_lock:
        if not ok:
            count, since = _failed.get(username, (0, 0.0))
            if time.time() - since >= LOCKOUT_SECONDS:
                count, since = 0, time.time()
            _failed[username] = (count + 1, since)
            raise HTTPException(status_code=401, detail="Incorrect username or password.")
        _failed.pop(username, None)

    return {"username": username, "name": doctor["name"]}


# ── Tokens ───────────────────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_token(doctor: dict) -> str:
    payload = _b64(json.dumps({
        "sub": doctor["username"],
        "name": doctor["name"],
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }).encode())
    signature = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def verify_token(token: str) -> Optional[dict]:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
    except Exception:
        return None
    if data.get("exp", 0) < time.time():
        return None
    # A removed account loses access immediately.
    if data.get("sub") not in _load_doctors():
        return None
    return {"username": data["sub"], "name": data["name"]}


def current_doctor(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency: the signed-in doctor, or 401."""
    if not REQUIRE_LOGIN:
        return GUEST_DOCTOR
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please sign in.")
    doctor = verify_token(authorization[7:].strip())
    if doctor is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
    return doctor


# ── Command line ─────────────────────────────────────────────────────────

def _cli(argv: list[str]) -> None:
    usage = __doc__.split("Manage accounts from the command line:")[1]
    if not argv:
        print(usage)
        return
    cmd, args = argv[0], argv[1:]
    doctors = _load_doctors()

    if cmd == "add" and len(args) == 2:
        username, name = args[0].strip().lower(), args[1].strip()
        password = getpass.getpass(f"Password for {username}: ")
        if len(password) < 8:
            sys.exit("Password must be at least 8 characters.")
        if getpass.getpass("Repeat password: ") != password:
            sys.exit("Passwords do not match.")
        salt, digest = hash_password(password)
        doctors[username] = {"name": name, "salt": salt, "hash": digest}
        _save_doctors(doctors)
        print(f"Saved {name} ({username}).")
    elif cmd == "remove" and len(args) == 1:
        if doctors.pop(args[0].strip().lower(), None) is None:
            sys.exit("No such user.")
        _save_doctors(doctors)
        print("Removed.")
    elif cmd == "list":
        for username, d in doctors.items():
            print(f"{username:<16} {d['name']}")
    else:
        print(usage)


if __name__ == "__main__":
    _cli(sys.argv[1:])

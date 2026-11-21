"""
Basic staff login for the clinic dashboard (judge item #5). Demo-grade, standard library only:
  * passwords are PBKDF2-hashed at startup and compared in constant time
  * sessions are HMAC-signed tokens that expire after 8 hours
  * roles: "doctor" can approve summaries; "nurse" / "front_desk" can view the queue, alerts and questions
A real product would use the clinic's SSO, MFA and audited access controls (see docs/JUDGE_PREP.md).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

TOKEN_TTL = 8 * 3600
_SECRET = (os.environ.get("CAREBRIDGE_SECRET") or secrets.token_hex(32)).encode()
_DEMO_PASSWORD = os.environ.get("CAREBRIDGE_DEMO_PASSWORD", "carebridge-demo")

DEMO_USERS = {
    "dr.demo": {"name": "Dr. Demo (Test Clinician)", "role": "doctor"},
    "nurse.demo": {"name": "Nurse Demo (Test Staff)", "role": "nurse"},
    "frontdesk.demo": {"name": "Front Desk Demo (Test Staff)", "role": "front_desk"},
}


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


_SALT = secrets.token_bytes(16)
_HASHES = {u: _hash(_DEMO_PASSWORD, _SALT) for u in DEMO_USERS}


def login(username: str, password: str) -> dict | None:
    username = (username or "").strip().lower()
    expected = _HASHES.get(username)
    attempt = _hash(password or "", _SALT)
    if expected is None or not hmac.compare_digest(expected, attempt):
        return None
    user = {"username": username, **DEMO_USERS[username]}
    payload = base64.urlsafe_b64encode(json.dumps({**user, "exp": int(time.time()) + TOKEN_TTL}).encode()).decode()
    sig = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return {"token": f"{payload}.{sig}", "user": user}


def verify(header: str | None) -> dict | None:
    if not header or not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    payload, _, sig = token.rpartition(".")
    if not payload or not hmac.compare_digest(hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest(), sig):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, json.JSONDecodeError):
        return None
    if data.get("exp", 0) < time.time():
        return None
    return data

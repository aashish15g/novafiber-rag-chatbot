from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
ACCESS_COOKIE = "access_token"
CSRF_COOKIE = "csrf_token"


def hash_password(password):
    """Hash a password with Argon2."""
    return password_hasher.hash(password)


def verify_password(password, password_hash):
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id, secret, csrf_token, expires_minutes=30):
    """Sign a short-lived JWT for a user."""
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id, "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "iss": "novafiber", "csrf": csrf_token
    }, secret, algorithm="HS256")


def verify_access_token(token, secret):
    """Verify the signature, issuer, and expiry before returning claims."""
    return jwt.decode(token, secret, algorithms=["HS256"], issuer="novafiber",
                      options={"require": ["sub", "iat", "exp", "csrf"]})

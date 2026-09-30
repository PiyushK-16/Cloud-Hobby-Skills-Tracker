"""Authentication service: password hashing + JWT access tokens (stateless) with a logout blacklist."""
import hashlib
import hmac
import os
import time
import uuid

import jwt

from backend.utils.config import settings

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: str) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "jti": uuid.uuid4().hex, "iat": now,
               "exp": now + settings.TOKEN_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

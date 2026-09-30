"""Authentication dependency: validates the Bearer token and loads the current user."""
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cloud.auth_service import decode_token
from cloud.database_service import db

bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    if "sub" not in payload or "jti" not in payload:
        raise HTTPException(401, "Invalid token")
    with db() as c:
        if c.execute("SELECT 1 FROM token_blacklist WHERE jti=?", (payload["jti"],)).fetchone():
            raise HTTPException(401, "Session ended. Please log in again.")
        row = c.execute("SELECT * FROM users WHERE user_id=?", (payload["sub"],)).fetchone()
    if row is None:
        raise HTTPException(401, "User no longer exists")
    user = dict(row)
    user["_jti"], user["_exp"] = payload["jti"], payload["exp"]
    return user

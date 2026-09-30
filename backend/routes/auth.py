"""AUTH: register / login / logout."""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.middleware.auth import current_user
from backend.models.schemas import LoginIn, RegisterIn
from backend.utils.helpers import clean_text, new_id, now_iso, rate_limit
from cloud.auth_service import create_token, hash_password, verify_password
from cloud.database_service import db

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterIn, request: Request):
    rate_limit(request, "register")
    email, username = body.email.lower(), body.username.lower()
    uid = new_id()
    try:
        with db() as c:
            if c.execute("SELECT 1 FROM users WHERE email=? OR username=?", (email, username)).fetchone():
                raise HTTPException(409, "Email or username already registered")
            c.execute("INSERT INTO users(user_id,name,username,email,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                      (uid, clean_text(body.name), username, email, hash_password(body.password), now_iso()))
    except sqlite3.IntegrityError:  # two simultaneous requests
        raise HTTPException(409, "Email or username already registered")
    return {"user_id": uid, "username": username, "message": "Registered successfully"}


@router.post("/login")
def login(body: LoginIn, request: Request):
    rate_limit(request, "login")
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (body.email.lower(),)).fetchone()
    if not u or not verify_password(body.password, u["password_hash"]):
        raise HTTPException(401, "Invalid email or password")  # same message: no account enumeration
    return {"access_token": create_token(u["user_id"]), "token_type": "bearer",
            "user": {"user_id": u["user_id"], "username": u["username"], "name": u["name"]}}


@router.post("/logout")
def logout(user=Depends(current_user)):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO token_blacklist(jti,expires_at) VALUES(?,?)", (user["_jti"], user["_exp"]))
        c.execute("DELETE FROM token_blacklist WHERE expires_at < strftime('%s','now')")
    return {"message": "Logged out"}

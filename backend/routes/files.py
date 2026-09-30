"""FILES: secure upload (type/size/magic-byte checks), signed-URL download, delete."""
import logging
import time

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.middleware.auth import current_user
from backend.services.file_service import detect_type, file_url
from backend.utils.config import settings
from backend.utils.helpers import new_id, now_iso
from cloud import storage_service
from cloud.database_service import db
from cloud.storage_service import StorageError

log = logging.getLogger("files")
router = APIRouter(prefix="/api/files", tags=["files"])
PURPOSES = {"profile", "post", "skill", "certificate"}


@router.post("/upload", status_code=201)
async def upload(file: UploadFile = File(...), purpose: str = Form("post"), user=Depends(current_user)):
    if purpose not in PURPOSES:
        raise HTTPException(422, f"purpose must be one of {sorted(PURPOSES)}")
    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large (max {settings.MAX_UPLOAD_BYTES // 1024 // 1024} MB)")
    if not data:
        raise HTTPException(400, "Empty file")
    kind = detect_type(data)  # trust the bytes, not the filename or client content-type
    if not kind or (purpose == "profile" and kind[0] == "pdf"):
        raise HTTPException(415, "Unsupported file type. Allowed: JPG, PNG, GIF, WEBP (and PDF for certificates)")
    ext, ctype = kind
    fid = new_id()
    key = f"users/{user['user_id']}/{purpose}/{fid}.{ext}"
    try:
        storage_service.upload_file(key, data, ctype)  # step 1: bytes -> object storage
    except StorageError:
        log.exception("storage upload failed")
        raise HTTPException(503, "File storage is temporarily unavailable. Please try again.")
    try:
        with db() as c:  # step 2: metadata -> database
            c.execute("INSERT INTO files(file_id,user_id,purpose,storage_key,content_type,size_bytes,created_at)"
                      " VALUES(?,?,?,?,?,?,?)", (fid, user["user_id"], purpose, key, ctype, len(data), now_iso()))
    except Exception:
        log.exception("db write failed after upload - cleaning up object %s", key)
        try:
            storage_service.delete_file(key)  # compensating action: no orphan objects
        except StorageError:
            log.error("orphan object left in storage: %s", key)
        raise
    return {"file_id": fid, "url": file_url(fid, key), "content_type": ctype, "size_bytes": len(data)}


@router.get("/content/{token}")
def content(token: str):
    """Serves local files for a valid, unexpired signed token (used as <img src>)."""
    try:
        p = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if p.get("typ") != "file":
            raise jwt.InvalidTokenError()
    except jwt.ExpiredSignatureError:
        raise HTTPException(403, "Link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(403, "Invalid link")
    with db() as c:
        f = c.execute("SELECT * FROM files WHERE file_id=?", (p["fid"],)).fetchone()
    if not f:
        raise HTTPException(404, "File not found")
    try:
        body = storage_service.get_file(f["storage_key"])
    except StorageError:
        raise HTTPException(503, "File storage is temporarily unavailable")
    return Response(body, media_type=f["content_type"], headers={"X-Content-Type-Options": "nosniff",
                                                                 "Cache-Control": "private, max-age=300"})


@router.delete("/{file_id}")
def delete(file_id: str, user=Depends(current_user)):
    with db() as c:
        f = c.execute("SELECT * FROM files WHERE file_id=? AND user_id=?", (file_id, user["user_id"])).fetchone()
        if not f:
            raise HTTPException(404, "File not found")
        c.execute("UPDATE users SET profile_picture=NULL WHERE profile_picture=?", (file_id,))
        c.execute("DELETE FROM files WHERE file_id=?", (file_id,))
    try:
        storage_service.delete_file(f["storage_key"])
    except StorageError:
        log.error("could not delete object %s (will need cleanup job)", f["storage_key"])
    return {"message": "File deleted"}

"""PROFILE: own profile (private) and public profiles."""
from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_user
from backend.models.schemas import ProfileUpdate
from backend.services.file_service import file_url
from backend.utils.helpers import clean_text
from cloud.database_service import db

router = APIRouter(prefix="/api", tags=["profile"])


def _avatar(c, file_id):
    if not file_id:
        return None
    f = c.execute("SELECT file_id, storage_key FROM files WHERE file_id=?", (file_id,)).fetchone()
    return file_url(f["file_id"], f["storage_key"]) if f else None


@router.get("/profile")
def get_profile(user=Depends(current_user)):
    with db() as c:
        url = _avatar(c, user["profile_picture"])
    return {"user_id": user["user_id"], "name": user["name"], "username": user["username"], "email": user["email"],
            "bio": user["bio"], "interests": user["interests"], "is_public": bool(user["is_public"]),
            "profile_picture_url": url, "created_at": user["created_at"]}


@router.put("/profile")
def update_profile(body: ProfileUpdate, user=Depends(current_user)):
    data = body.model_dump(exclude_unset=True)
    with db() as c:
        if "profile_picture_file_id" in data:
            fid = data.pop("profile_picture_file_id")
            if fid and not c.execute("SELECT 1 FROM files WHERE file_id=? AND user_id=? AND purpose='profile'",
                                     (fid, user["user_id"])).fetchone():
                raise HTTPException(400, "Unknown profile image file")
            data["profile_picture"] = fid
        if "is_public" in data:
            data["is_public"] = int(data["is_public"])
        for k in ("name", "bio", "interests"):
            if k in data:
                data[k] = clean_text(data[k])
        if data:
            sets = ", ".join(f"{k}=?" for k in data)  # keys come from the schema, never from the client
            c.execute(f"UPDATE users SET {sets} WHERE user_id=?", (*data.values(), user["user_id"]))
    return get_profile(current_user_reload(user["user_id"]))


def current_user_reload(uid):
    with db() as c:
        return dict(c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone())


@router.get("/users/{username}")
def public_profile(username: str, viewer=Depends(current_user)):
    """Public view: never returns email or password hash."""
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone()
        if not u:
            raise HTTPException(404, "User not found")
        if not u["is_public"] and u["user_id"] != viewer["user_id"]:
            return {"username": u["username"], "private": True}
        n = lambda sql: c.execute(sql, (u["user_id"],)).fetchone()[0]
        return {"username": u["username"], "name": u["name"], "bio": u["bio"], "interests": u["interests"],
                "profile_picture_url": _avatar(c, u["profile_picture"]), "private": False,
                "posts": n("SELECT COUNT(*) FROM posts WHERE user_id=?"),
                "followers": n("SELECT COUNT(*) FROM follows WHERE following_id=?"),
                "following": n("SELECT COUNT(*) FROM follows WHERE follower_id=?"),
                "is_following": bool(c.execute("SELECT 1 FROM follows WHERE follower_id=? AND following_id=?",
                                               (viewer["user_id"], u["user_id"])).fetchone())}

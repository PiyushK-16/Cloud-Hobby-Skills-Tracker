"""COMMUNITY: createPost, getCommunityFeed, deleteOwnPost, trending skills."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.middleware.auth import current_user
from backend.models.schemas import PostIn
from backend.routes.skills import owned_skill
from backend.services.file_service import file_url
from backend.utils.helpers import clean_text, new_id, now_iso
from cloud import storage_service
from cloud.database_service import db

log = logging.getLogger("posts")
router = APIRouter(prefix="/api", tags=["community"])

FEED_SQL = """
SELECT p.post_id, p.user_id, p.content, p.created_at, p.skill_id, p.milestone_id,
       u.username, s.skill_name, s.category,
       f.file_id AS media_id, f.storage_key AS media_key,
       a.file_id AS avatar_id, a.storage_key AS avatar_key,
       (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.post_id) AS like_count,
       (SELECT COUNT(*) FROM comments cm WHERE cm.post_id=p.post_id) AS comment_count,
       EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.post_id AND l.user_id=?) AS liked_by_me
FROM posts p
JOIN users u ON u.user_id=p.user_id
LEFT JOIN skills s ON s.skill_id=p.skill_id
LEFT JOIN files f ON f.file_id=p.file_id
LEFT JOIN files a ON a.file_id=u.profile_picture
"""


def _shape(r, viewer_id):
    return {"post_id": r["post_id"], "user_id": r["user_id"], "username": r["username"],
            "avatar_url": file_url(r["avatar_id"], r["avatar_key"]), "skill_id": r["skill_id"],
            "skill_name": r["skill_name"], "category": r["category"], "content": r["content"],
            "media_url": file_url(r["media_id"], r["media_key"]), "created_at": r["created_at"],
            "like_count": r["like_count"], "comment_count": r["comment_count"],
            "liked_by_me": bool(r["liked_by_me"]), "is_mine": r["user_id"] == viewer_id,
            "is_milestone": bool(r["milestone_id"])}


@router.post("/posts", status_code=201)
def create_post(body: PostIn, user=Depends(current_user)):
    pid, uid = new_id(), user["user_id"]
    with db() as c:
        if body.skill_id:
            owned_skill(c, body.skill_id, uid)
        if body.file_id and not c.execute("SELECT 1 FROM files WHERE file_id=? AND user_id=?", (body.file_id, uid)).fetchone():
            raise HTTPException(400, "Unknown file")
        if body.milestone_id and not c.execute(
                "SELECT 1 FROM milestones m JOIN goals g ON g.goal_id=m.goal_id WHERE m.milestone_id=? AND g.user_id=?",
                (body.milestone_id, uid)).fetchone():
            raise HTTPException(400, "Unknown milestone")
        c.execute("INSERT INTO posts(post_id,user_id,skill_id,milestone_id,file_id,content,created_at) VALUES(?,?,?,?,?,?,?)",
                  (pid, uid, body.skill_id, body.milestone_id, body.file_id, clean_text(body.content), now_iso()))
        row = c.execute(FEED_SQL + " WHERE p.post_id=?", (uid, pid)).fetchone()
        return _shape(row, uid)


@router.get("/feed")
def get_community_feed(category: Optional[str] = None, q: Optional[str] = None,
                       sort: str = Query("recent", pattern="^(recent|liked)$"), following: bool = False,
                       limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0), user=Depends(current_user)):
    uid = user["user_id"]
    where, args = [], [uid]
    if category and category != "All":
        where.append("s.category=?"); args.append(category)
    if q:
        where.append("(p.content LIKE ? OR s.skill_name LIKE ?)"); args += [f"%{q}%", f"%{q}%"]
    if following:
        where.append("p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?)"); args.append(uid)
    sql = FEED_SQL + (" WHERE " + " AND ".join(where) if where else "")
    sql += " ORDER BY " + ("like_count DESC, p.created_at DESC" if sort == "liked" else "p.created_at DESC")
    with db() as c:
        rows = c.execute(sql + " LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()
        return [_shape(r, uid) for r in rows]


@router.delete("/posts/{post_id}")
def delete_own_post(post_id: str, user=Depends(current_user)):
    with db() as c:
        p = c.execute("SELECT post_id, user_id, file_id FROM posts WHERE post_id=?", (post_id,)).fetchone()
        if not p:
            raise HTTPException(404, "Post not found")
        if p["user_id"] != user["user_id"] and not user["is_admin"]:
            raise HTTPException(403, "You can only delete your own posts")
        f = c.execute("SELECT * FROM files WHERE file_id=?", (p["file_id"],)).fetchone() if p["file_id"] else None
        c.execute("DELETE FROM posts WHERE post_id=?", (post_id,))
        if f:
            c.execute("DELETE FROM files WHERE file_id=?", (f["file_id"],))
    if f:
        try:
            storage_service.delete_file(f["storage_key"])
        except Exception:
            log.error("could not remove object %s", f["storage_key"])
    return {"message": "Post deleted"}


@router.get("/community/trending")
def trending_skills(user=Depends(current_user)):
    with db() as c:
        rows = c.execute("SELECT s.skill_name AS skill, s.category, COUNT(*) AS posts FROM posts p JOIN skills s "
                         "ON s.skill_id=p.skill_id GROUP BY LOWER(s.skill_name) ORDER BY posts DESC LIMIT 5").fetchall()
        return [dict(r) for r in rows]

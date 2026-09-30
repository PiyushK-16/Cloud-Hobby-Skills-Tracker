"""SOCIAL: likes, comments, follows, reports."""
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.middleware.auth import current_user
from backend.models.schemas import CommentIn, ReportIn
from backend.utils.helpers import clean_text, new_id, now_iso
from cloud.database_service import db

router = APIRouter(prefix="/api", tags=["social"])


def _post_exists(c, post_id):
    if not c.execute("SELECT 1 FROM posts WHERE post_id=?", (post_id,)).fetchone():
        raise HTTPException(404, "Post not found")


def _likes(c, post_id):
    return c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,)).fetchone()[0]


@router.post("/posts/{post_id}/like")
def like_post(post_id: str, user=Depends(current_user)):
    with db() as c:
        _post_exists(c, post_id)
        # PRIMARY KEY(post_id,user_id) + INSERT OR IGNORE => liking twice is idempotent (no duplicates)
        c.execute("INSERT OR IGNORE INTO likes(post_id,user_id,created_at) VALUES(?,?,?)", (post_id, user["user_id"], now_iso()))
        return {"liked": True, "like_count": _likes(c, post_id)}


@router.delete("/posts/{post_id}/like")
def unlike_post(post_id: str, user=Depends(current_user)):
    with db() as c:
        _post_exists(c, post_id)
        c.execute("DELETE FROM likes WHERE post_id=? AND user_id=?", (post_id, user["user_id"]))
        return {"liked": False, "like_count": _likes(c, post_id)}


@router.post("/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: str, body: CommentIn, user=Depends(current_user)):
    cid = new_id()
    with db() as c:
        _post_exists(c, post_id)
        c.execute("INSERT INTO comments(comment_id,post_id,user_id,content,created_at) VALUES(?,?,?,?,?)",
                  (cid, post_id, user["user_id"], clean_text(body.content), now_iso()))
    return {"comment_id": cid, "post_id": post_id, "username": user["username"], "content": clean_text(body.content)}


@router.get("/posts/{post_id}/comments")
def get_comments(post_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                 user=Depends(current_user)):
    with db() as c:
        _post_exists(c, post_id)
        rows = c.execute("SELECT cm.comment_id, cm.user_id, u.username, cm.content, cm.created_at FROM comments cm "
                         "JOIN users u ON u.user_id=cm.user_id WHERE cm.post_id=? ORDER BY cm.created_at LIMIT ? OFFSET ?",
                         (post_id, limit, offset)).fetchall()
        return [{**dict(r), "is_mine": r["user_id"] == user["user_id"]} for r in rows]


@router.delete("/comments/{comment_id}")
def delete_own_comment(comment_id: str, user=Depends(current_user)):
    with db() as c:
        row = c.execute("SELECT user_id FROM comments WHERE comment_id=?", (comment_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Comment not found")
        if row["user_id"] != user["user_id"] and not user["is_admin"]:
            raise HTTPException(403, "You can only delete your own comments")
        c.execute("DELETE FROM comments WHERE comment_id=?", (comment_id,))
    return {"message": "Comment deleted"}


@router.post("/posts/{post_id}/report", status_code=201)
def report_post(post_id: str, body: ReportIn, user=Depends(current_user)):
    with db() as c:
        _post_exists(c, post_id)
        c.execute("INSERT INTO reports(report_id,post_id,reporter_id,reason,created_at) VALUES(?,?,?,?,?)",
                  (new_id(), post_id, user["user_id"], clean_text(body.reason), now_iso()))
    return {"message": "Thanks - the post was reported for review"}


def _target(c, username):
    t = c.execute("SELECT user_id FROM users WHERE username=?", (username.lower(),)).fetchone()
    if not t:
        raise HTTPException(404, "User not found")
    return t["user_id"]


@router.post("/users/{username}/follow")
def follow_user(username: str, user=Depends(current_user)):
    with db() as c:
        tid = _target(c, username)
        if tid == user["user_id"]:
            raise HTTPException(400, "You cannot follow yourself")
        c.execute("INSERT OR IGNORE INTO follows(follower_id,following_id,created_at) VALUES(?,?,?)", (user["user_id"], tid, now_iso()))
    return {"following": True}


@router.delete("/users/{username}/follow")
def unfollow_user(username: str, user=Depends(current_user)):
    with db() as c:
        c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (user["user_id"], _target(c, username)))
    return {"following": False}


@router.get("/users/{username}/followers")
def get_followers(username: str, user=Depends(current_user)):
    with db() as c:
        rows = c.execute("SELECT u.username, u.name FROM follows f JOIN users u ON u.user_id=f.follower_id "
                         "WHERE f.following_id=?", (_target(c, username),)).fetchall()
        return [dict(r) for r in rows]


@router.get("/users/{username}/following")
def get_following(username: str, user=Depends(current_user)):
    with db() as c:
        rows = c.execute("SELECT u.username, u.name FROM follows f JOIN users u ON u.user_id=f.following_id "
                         "WHERE f.follower_id=?", (_target(c, username),)).fetchall()
        return [dict(r) for r in rows]

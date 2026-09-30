"""Automated tests mapped to the TC-xx IDs in docs/testing.md."""
import sqlite3
import time
from datetime import date, timedelta

import jwt
import pytest

from analytics.progress_service import compute_streaks, progress_pct
from tests.conftest import PNG, make_skill, signup


def test_tc01_register(client):
    r = client.post("/api/register", json={"name": "A", "username": "anna", "email": "a@x.com", "password": "Dummy#Pass123"})
    assert r.status_code == 201 and "password" not in r.text


def test_tc02_duplicate_registration(client):
    signup(client, "anna")
    r = client.post("/api/register", json={"name": "A", "username": "anna", "email": "anna@example.com", "password": "Dummy#Pass123"})
    assert r.status_code == 409


def test_tc03_04_login(client):
    signup(client, "anna")
    assert client.post("/api/login", json={"email": "anna@example.com", "password": "Dummy#Pass123"}).status_code == 200
    assert client.post("/api/login", json={"email": "anna@example.com", "password": "wrong"}).status_code == 401


def test_tc05_profile_update(client):
    h = signup(client)
    r = client.put("/api/profile", headers=h, json={"bio": "I love photos", "interests": "art"})
    assert r.status_code == 200 and r.json()["bio"] == "I love photos"


def test_tc06_07_08_skill_crud(client):
    h = signup(client)
    sid = make_skill(client, h)
    assert client.put(f"/api/skills/{sid}", headers=h, json={"status": "PAUSED"}).json()["status"] == "PAUSED"
    assert client.get(f"/api/skills/{sid}", headers=h).status_code == 200
    assert client.delete(f"/api/skills/{sid}", headers=h).status_code == 200
    assert client.get("/api/skills", headers=h).json() == []
    assert client.post("/api/skills", headers=h, json={"skill_name": "x", "current_level": "GOD"}).status_code == 422


def _goal(client, h, sid, target=20):
    return client.post("/api/goals", headers=h, json={"skill_id": sid, "title": "Practice", "target_value": target,
                                                      "unit": "hours", "milestones": [1, 5, 20]}).json()


def test_tc09_10_11_12_goal_practice_progress_milestone(client):
    h = signup(client)
    sid = make_skill(client, h)
    g = _goal(client, h, sid)
    r = client.post("/api/practice", headers=h, json={"skill_id": sid, "duration_minutes": 60, "activity": "Portraits"}).json()
    assert r["milestones_achieved"] == ["1 hours"]
    goal = client.get("/api/goals", headers=h).json()[0]
    assert goal["current_value"] == 1 and goal["progress_pct"] == 5.0
    client.post("/api/practice", headers=h, json={"skill_id": sid, "duration_minutes": 19 * 60, "activity": "Marathon"})
    goal = client.get("/api/goals", headers=h).json()[0]
    assert goal["status"] == "COMPLETED" and goal["progress_pct"] == 100.0
    assert client.post("/api/practice", headers=h, json={"skill_id": sid, "duration_minutes": 0, "activity": "x"}).status_code == 422


def test_progress_and_streak_math():
    assert progress_pct(18, 30) == 60.0 and progress_pct(45, 30) == 100.0 and progress_pct(1, 0) == 0.0
    t = date(2026, 9, 30)
    days = [t, t - timedelta(1), t - timedelta(2), t - timedelta(5), t - timedelta(6)]
    assert compute_streaks(days, t) == (3, 3)
    assert compute_streaks([t - timedelta(1)], t) == (1, 1)      # yesterday keeps the streak alive
    assert compute_streaks([t - timedelta(2)], t) == (0, 1)      # broken
    assert compute_streaks([t, t], t) == (1, 1)                  # same day counts once


def test_tc13_14_upload(client):
    h = signup(client)
    ok = client.post("/api/files/upload", headers=h, files={"file": ("a.png", PNG, "image/png")}, data={"purpose": "post"})
    assert ok.status_code == 201
    assert client.get(ok.json()["url"]).content == PNG                       # signed URL works
    bad = client.post("/api/files/upload", headers=h, files={"file": ("a.png", b"<script>alert(1)</script>", "image/png")})
    assert bad.status_code == 415                                            # extension/content-type lies are ignored
    assert client.get("/api/files/content/not-a-token").status_code == 403


def test_tc15_16_post_and_feed(client):
    h = signup(client)
    sid = make_skill(client, h)
    fid = client.post("/api/files/upload", headers=h, files={"file": ("a.png", PNG, "image/png")}).json()["file_id"]
    p = client.post("/api/posts", headers=h, json={"content": "30 hours!", "skill_id": sid, "file_id": fid})
    assert p.status_code == 201 and p.json()["media_url"]
    feed = client.get("/api/feed", headers=h).json()
    assert feed[0]["content"] == "30 hours!" and feed[0]["skill_name"] == "Photography"
    assert client.get("/api/feed?category=Music", headers=h).json() == []
    assert len(client.get("/api/feed?q=hours", headers=h).json()) == 1


def test_tc17_18_19_likes(client):
    a, b = signup(client, "alice"), signup(client, "bob")
    pid = client.post("/api/posts", headers=a, json={"content": "hi"}).json()["post_id"]
    assert client.post(f"/api/posts/{pid}/like", headers=b).json()["like_count"] == 1
    assert client.post(f"/api/posts/{pid}/like", headers=b).json()["like_count"] == 1   # duplicate prevented
    assert client.delete(f"/api/posts/{pid}/like", headers=b).json()["like_count"] == 0


def test_tc20_21_comments_and_unauthorized_delete(client):
    a, b = signup(client, "alice"), signup(client, "bob")
    pid = client.post("/api/posts", headers=a, json={"content": "hi"}).json()["post_id"]
    cid = client.post(f"/api/posts/{pid}/comments", headers=b, json={"content": "nice"}).json()["comment_id"]
    assert client.get(f"/api/posts/{pid}/comments", headers=a).json()[0]["content"] == "nice"
    assert client.delete(f"/api/comments/{cid}", headers=a).status_code == 403   # not comment owner
    assert client.delete(f"/api/posts/{pid}", headers=b).status_code == 403      # not post owner
    assert client.delete(f"/api/comments/{cid}", headers=b).status_code == 200
    assert client.delete(f"/api/posts/{pid}", headers=a).status_code == 200


def test_tc22_analytics(client):
    h = signup(client)
    sid = make_skill(client, h)
    today = date.today()
    for d in (today, today - timedelta(1)):
        client.post("/api/practice", headers=h, json={"skill_id": sid, "duration_minutes": 90, "activity": "x",
                                                      "practiced_at": d.isoformat()})
    d = client.get("/api/analytics/dashboard", headers=h).json()
    assert d["total_practice_hours"] == 3.0 and d["current_streak"] == 2 and d["most_practiced_skill"] == "Photography"
    assert d["hours_by_skill"][0]["hours"] == 3.0 and len(d["weekly_trend"]) == 8


def test_tc23_user_data_isolation(client):
    a, b = signup(client, "alice"), signup(client, "bob")
    sid = make_skill(client, a)
    assert client.get(f"/api/skills/{sid}", headers=b).status_code == 404
    assert client.put(f"/api/skills/{sid}", headers=b, json={"status": "PAUSED"}).status_code == 404
    assert client.post("/api/practice", headers=b, json={"skill_id": sid, "duration_minutes": 5, "activity": "x"}).status_code == 404
    assert client.get("/api/skills", headers=b).json() == []
    assert "email" not in client.get("/api/users/alice", headers=b).json()          # public API hides private data


def test_tc24_storage_failure(client, monkeypatch):
    from cloud import storage_service
    h = signup(client)

    class Broken:
        def put(self, *a): raise storage_service.StorageError("down")
        def presigned_url(self, *a): return None

    monkeypatch.setattr(storage_service, "get_storage", lambda: Broken())
    r = client.post("/api/files/upload", headers=h, files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 503 and "temporarily" in r.json()["detail"]


def test_tc25_database_failure(client, monkeypatch):
    h = signup(client)

    def broken():
        raise sqlite3.OperationalError("db down")

    monkeypatch.setattr("backend.routes.skills.db", broken)
    r = client.get("/api/skills", headers=h)
    assert r.status_code == 503 and "database" in r.json()["detail"].lower()


def test_upload_db_failure_cleans_up_object(client, monkeypatch, tmp_path):
    import os
    h = signup(client)

    def broken():
        raise sqlite3.OperationalError("db down")

    monkeypatch.setattr("backend.routes.files.db", broken)
    r = client.post("/api/files/upload", headers=h, files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 503
    left = [f for _, _, fs in os.walk(tmp_path / "uploads") for f in fs]
    assert left == []                                   # compensating delete removed the orphan object


def test_tc26_token_expiry(client):
    h = signup(client)
    uid = client.get("/api/profile", headers=h).json()["user_id"]
    now = int(time.time())
    old = jwt.encode({"sub": uid, "jti": "x", "iat": now - 100, "exp": now - 10},
                     "test-secret-key-for-pytest-only-0123456789", algorithm="HS256")
    r = client.get("/api/profile", headers={"Authorization": f"Bearer {old}"})
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()
    assert client.get("/api/profile").status_code == 401


def test_tc27_logout(client):
    h = signup(client)
    assert client.post("/api/logout", headers=h).status_code == 200
    assert client.get("/api/profile", headers=h).status_code == 401


def test_follow_and_following_feed(client):
    a, b = signup(client, "alice"), signup(client, "bob")
    client.post("/api/posts", headers=a, json={"content": "from alice"})
    client.post("/api/posts", headers=b, json={"content": "from bob"})
    assert client.post("/api/users/alice/follow", headers=b).status_code == 200
    assert client.post("/api/users/bob/follow", headers=b).status_code == 400
    feed = client.get("/api/feed?following=true", headers=b).json()
    assert [p["content"] for p in feed] == ["from alice"]
    assert client.get("/api/users/alice/followers", headers=b).json()[0]["username"] == "bob"

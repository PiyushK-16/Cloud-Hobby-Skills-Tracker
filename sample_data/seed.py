"""Creates SYNTHETIC demo users/content through the real API. Run from project root: python sample_data/seed.py
Demo password below is a dummy value for local development only."""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SECRET_KEY", "dev-only-seed-key-please-use-env-file")
os.environ.setdefault("RATE_LIMIT_PER_MIN", "1000")
from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from fastapi.testclient import TestClient  # noqa: E402
from backend.app import app  # noqa: E402

PW = "Demo#Pass123"
USERS = [("asha", "Asha Demo", "Photography"), ("ben", "Ben Demo", "Music"), ("chloe", "Chloe Demo", "Coding")]

with TestClient(app) as c:
    heads = {}
    for u, name, _ in USERS:
        c.post("/api/register", json={"name": name, "username": u, "email": f"{u}@example.com", "password": PW})
        tok = c.post("/api/login", json={"email": f"{u}@example.com", "password": PW}).json()["access_token"]
        heads[u] = {"Authorization": f"Bearer {tok}"}
    posts = []
    for u, _, skill in USERS:
        h = heads[u]
        sid = c.post("/api/skills", headers=h, json={"skill_name": skill, "category": skill}).json()["skill_id"]
        c.post("/api/goals", headers=h, json={"skill_id": sid, "title": f"Practice 20 hours of {skill}", "target_value": 20,
                                               "unit": "hours", "milestones": [5, 10, 20]})
        for i in range(6):
            c.post("/api/practice", headers=h, json={"skill_id": sid, "duration_minutes": 60 + 15 * i, "activity": f"{skill} drill {i+1}",
                                                     "practiced_at": (date.today() - timedelta(days=i)).isoformat()})
        posts.append(c.post("/api/posts", headers=h, json={"content": f"Week of {skill} practice done!", "skill_id": sid}).json()["post_id"])
    for pid in posts:
        c.post(f"/api/posts/{pid}/like", headers=heads["ben"])
        c.post(f"/api/posts/{pid}/comments", headers=heads["chloe"], json={"content": "Great progress!"})
    c.post("/api/users/asha/follow", headers=heads["ben"])
print("Seeded users: asha / ben / chloe  (password:", PW, ")")

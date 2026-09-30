"""Database service. SQLite locally; the same SQL schema works on PostgreSQL (Supabase/RDS) with minor changes."""
import os
import sqlite3
from contextlib import contextmanager

from backend.utils.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  user_id TEXT PRIMARY KEY, name TEXT NOT NULL, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL, profile_picture TEXT, bio TEXT DEFAULT '', interests TEXT DEFAULT '',
  is_public INTEGER NOT NULL DEFAULT 1, is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(
  file_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  purpose TEXT NOT NULL, storage_key TEXT NOT NULL UNIQUE, content_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS skills(
  skill_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  skill_name TEXT NOT NULL, category TEXT NOT NULL, current_level TEXT NOT NULL, target_level TEXT NOT NULL,
  start_date TEXT, target_date TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', description TEXT DEFAULT '',
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS goals(
  goal_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  skill_id TEXT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE, title TEXT NOT NULL,
  target_value REAL NOT NULL, current_value REAL NOT NULL DEFAULT 0, unit TEXT NOT NULL,
  deadline TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS milestones(
  milestone_id TEXT PRIMARY KEY, goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
  title TEXT NOT NULL, target_value REAL NOT NULL, achieved INTEGER NOT NULL DEFAULT 0, achieved_at TEXT);
CREATE TABLE IF NOT EXISTS practice_sessions(
  session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  skill_id TEXT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE, duration_minutes INTEGER NOT NULL,
  activity TEXT NOT NULL, notes TEXT DEFAULT '', practiced_at TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS posts(
  post_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  skill_id TEXT REFERENCES skills(skill_id) ON DELETE SET NULL,
  milestone_id TEXT REFERENCES milestones(milestone_id) ON DELETE SET NULL,
  file_id TEXT REFERENCES files(file_id) ON DELETE SET NULL, content TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS comments(
  comment_id TEXT PRIMARY KEY, post_id TEXT NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, content TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS likes(
  post_id TEXT NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, created_at TEXT NOT NULL,
  PRIMARY KEY(post_id, user_id));
CREATE TABLE IF NOT EXISTS follows(
  follower_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  following_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, created_at TEXT NOT NULL,
  PRIMARY KEY(follower_id, following_id), CHECK(follower_id <> following_id));
CREATE TABLE IF NOT EXISTS reports(
  report_id TEXT PRIMARY KEY, post_id TEXT NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
  reporter_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, reason TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS token_blacklist(jti TEXT PRIMARY KEY, expires_at INTEGER NOT NULL);

CREATE INDEX IF NOT EXISTS idx_skills_user ON skills(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_skill ON goals(skill_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON practice_sessions(user_id, practiced_at);
CREATE INDEX IF NOT EXISTS idx_sessions_skill ON practice_sessions(skill_id);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);
"""


def get_conn() -> sqlite3.Connection:
    path = settings.DATABASE_PATH
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    """Transaction scope: commit on success, rollback on any error."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(SCHEMA)

"""Small shared helpers: ids, timestamps, text cleaning, rate limiting."""
import re
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from backend.utils.config import settings

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def new_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value):
    """Trim and remove control characters. Output escaping is done by the frontend (textContent)."""
    if value is None:
        return None
    return _CONTROL.sub("", value).strip()


_hits = defaultdict(deque)


def rate_limit(request: Request, key: str) -> None:
    """Tiny in-memory sliding-window limiter (per IP + key). In production use Redis / API Gateway."""
    now = time.time()
    ip = request.client.host if request.client else "unknown"
    q = _hits[(ip, key)]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")
    q.append(now)

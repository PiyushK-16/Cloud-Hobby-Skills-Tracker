"""ANALYTICS: personal dashboard numbers for charts."""
from fastapi import APIRouter, Depends

from analytics.progress_service import build_dashboard
from backend.middleware.auth import current_user
from cloud.database_service import db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(user=Depends(current_user)):
    with db() as c:
        data = build_dashboard(c, user["user_id"])
    data["welcome"] = user["name"]
    return data

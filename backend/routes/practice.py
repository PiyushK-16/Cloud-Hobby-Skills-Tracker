"""PRACTICE sessions and GOALS / MILESTONES."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.middleware.auth import current_user
from backend.models.schemas import GoalIn, GoalUpdate, PracticeIn
from backend.routes.skills import owned_skill
from backend.services.tracking_service import apply_practice, goal_with_progress, refresh_goal
from backend.utils.helpers import clean_text, new_id, now_iso
from cloud.database_service import db

router = APIRouter(prefix="/api", tags=["practice"])


@router.post("/practice", status_code=201)
def log_practice(body: PracticeIn, user=Depends(current_user)):
    sid = new_id()
    day = (body.practiced_at or date.today()).isoformat()
    with db() as c:
        owned_skill(c, body.skill_id, user["user_id"])
        c.execute("INSERT INTO practice_sessions(session_id,user_id,skill_id,duration_minutes,activity,notes,practiced_at,"
                  "created_at) VALUES(?,?,?,?,?,?,?,?)",
                  (sid, user["user_id"], body.skill_id, body.duration_minutes, clean_text(body.activity),
                   clean_text(body.notes), day, now_iso()))
        effects = apply_practice(c, user["user_id"], body.skill_id, body.duration_minutes)
    return {"session_id": sid, "practiced_at": day, **effects}


@router.get("/practice")
def list_practice(skill_id: Optional[str] = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                  user=Depends(current_user)):
    sql = ("SELECT s.*, k.skill_name FROM practice_sessions s JOIN skills k ON k.skill_id=s.skill_id "
           "WHERE s.user_id=?")
    args = [user["user_id"]]
    if skill_id:
        sql += " AND s.skill_id=?"
        args.append(skill_id)
    with db() as c:
        rows = c.execute(sql + " ORDER BY s.practiced_at DESC, s.created_at DESC LIMIT ? OFFSET ?", (*args, limit, offset))
        return [dict(r) for r in rows.fetchall()]


@router.get("/skills/{skill_id}/practice")
def skill_practice(skill_id: str, user=Depends(current_user)):
    with db() as c:
        owned_skill(c, skill_id, user["user_id"])
        rows = c.execute("SELECT * FROM practice_sessions WHERE skill_id=? ORDER BY practiced_at DESC", (skill_id,))
        return [dict(r) for r in rows.fetchall()]


@router.post("/goals", status_code=201)
def create_goal(body: GoalIn, user=Depends(current_user)):
    gid = new_id()
    marks = sorted(set(body.milestones)) if body.milestones else [round(body.target_value * p, 2) for p in (.25, .5, .75, 1)]
    if any(m <= 0 or m > body.target_value for m in marks):
        raise HTTPException(422, "Milestones must be between 0 and the goal target")
    with db() as c:
        owned_skill(c, body.skill_id, user["user_id"])
        c.execute("INSERT INTO goals(goal_id,user_id,skill_id,title,target_value,current_value,unit,deadline,status,created_at)"
                  " VALUES(?,?,?,?,?,0,?,?, 'ACTIVE',?)",
                  (gid, user["user_id"], body.skill_id, clean_text(body.title), body.target_value,
                   clean_text(body.unit).lower(), body.deadline.isoformat() if body.deadline else None, now_iso()))
        for m in marks:
            c.execute("INSERT INTO milestones(milestone_id,goal_id,title,target_value) VALUES(?,?,?,?)",
                      (new_id(), gid, f"{m:g} {clean_text(body.unit).lower()}", m))
        return goal_with_progress(c, c.execute("SELECT * FROM goals WHERE goal_id=?", (gid,)).fetchone())


@router.get("/goals")
def list_goals(skill_id: Optional[str] = None, user=Depends(current_user)):
    sql, args = "SELECT g.*, k.skill_name FROM goals g JOIN skills k ON k.skill_id=g.skill_id WHERE g.user_id=?", [user["user_id"]]
    if skill_id:
        sql += " AND g.skill_id=?"
        args.append(skill_id)
    with db() as c:
        out = []
        for g in c.execute(sql + " ORDER BY g.created_at DESC", args).fetchall():
            d = goal_with_progress(c, g)
            d["skill_name"] = g["skill_name"]
            out.append(d)
        return out


@router.put("/goals/{goal_id}")
def update_goal(goal_id: str, body: GoalUpdate, user=Depends(current_user)):
    data = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in body.model_dump(exclude_unset=True).items()}
    if "title" in data:
        data["title"] = clean_text(data["title"])
    with db() as c:
        if not c.execute("SELECT 1 FROM goals WHERE goal_id=? AND user_id=?", (goal_id, user["user_id"])).fetchone():
            raise HTTPException(404, "Goal not found")
        if data:
            sets = ", ".join(f"{k}=?" for k in data)
            c.execute(f"UPDATE goals SET {sets} WHERE goal_id=?", (*data.values(), goal_id))
        refresh_goal(c, goal_id)
        return goal_with_progress(c, c.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone())

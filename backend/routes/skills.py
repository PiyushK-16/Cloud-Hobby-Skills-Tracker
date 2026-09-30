"""SKILLS: createSkill, updateSkill, deleteSkill, getMySkills, getSkillDetails."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_user
from backend.models.schemas import SkillIn, SkillUpdate
from backend.services.tracking_service import goal_with_progress
from backend.utils.helpers import clean_text, new_id, now_iso
from cloud.database_service import db

router = APIRouter(prefix="/api/skills", tags=["skills"])


def owned_skill(c, skill_id, user_id):
    """Return the skill only if it belongs to the user (404 otherwise -> no data leakage)."""
    row = c.execute("SELECT * FROM skills WHERE skill_id=? AND user_id=?", (skill_id, user_id)).fetchone()
    if not row:
        raise HTTPException(404, "Skill not found")
    return row


def _dump(body):
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in body.model_dump(exclude_unset=True).items()}


@router.post("", status_code=201)
def create_skill(body: SkillIn, user=Depends(current_user)):
    sid = new_id()
    d = body.model_dump()
    with db() as c:
        c.execute("INSERT INTO skills(skill_id,user_id,skill_name,category,current_level,target_level,start_date,"
                  "target_date,status,description,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (sid, user["user_id"], clean_text(d["skill_name"]), d["category"], d["current_level"], d["target_level"],
                   d["start_date"].isoformat() if d["start_date"] else None,
                   d["target_date"].isoformat() if d["target_date"] else None,
                   d["status"], clean_text(d["description"]), now_iso()))
        return dict(owned_skill(c, sid, user["user_id"]))


@router.get("")
def get_my_skills(status: Optional[str] = None, user=Depends(current_user)):
    sql, args = "SELECT * FROM skills WHERE user_id=?", [user["user_id"]]
    if status:
        sql += " AND status=?"
        args.append(status.upper())
    with db() as c:
        return [dict(r) for r in c.execute(sql + " ORDER BY created_at DESC", args).fetchall()]


@router.get("/{skill_id}")
def get_skill_details(skill_id: str, user=Depends(current_user)):
    with db() as c:
        s = dict(owned_skill(c, skill_id, user["user_id"]))
        agg = c.execute("SELECT COUNT(*) n, COALESCE(SUM(duration_minutes),0) m FROM practice_sessions WHERE skill_id=?",
                        (skill_id,)).fetchone()
        s["session_count"], s["total_minutes"] = agg["n"], agg["m"]
        s["goals"] = [goal_with_progress(c, g) for g in
                      c.execute("SELECT * FROM goals WHERE skill_id=?", (skill_id,)).fetchall()]
        return s


@router.put("/{skill_id}")
def update_skill(skill_id: str, body: SkillUpdate, user=Depends(current_user)):
    data = _dump(body)
    for k in ("skill_name", "description"):
        if k in data:
            data[k] = clean_text(data[k])
    with db() as c:
        owned_skill(c, skill_id, user["user_id"])
        if data:
            sets = ", ".join(f"{k}=?" for k in data)
            c.execute(f"UPDATE skills SET {sets} WHERE skill_id=?", (*data.values(), skill_id))
        return dict(owned_skill(c, skill_id, user["user_id"]))


@router.delete("/{skill_id}")
def delete_skill(skill_id: str, user=Depends(current_user)):
    with db() as c:
        owned_skill(c, skill_id, user["user_id"])
        c.execute("DELETE FROM skills WHERE skill_id=?", (skill_id,))  # cascades to sessions/goals/milestones
    return {"message": "Skill deleted"}

"""Business logic that links practice sessions -> goals -> milestones."""
from analytics.progress_service import progress_pct
from backend.utils.helpers import now_iso


def refresh_goal(c, goal_id: str) -> dict:
    """Mark milestones as achieved and complete the goal when its target is reached."""
    g = c.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
    result = {"milestones_achieved": [], "goal_completed": False}
    cur = g["current_value"]
    for m in c.execute("SELECT * FROM milestones WHERE goal_id=? AND achieved=0 AND target_value<=?",
                       (goal_id, cur)).fetchall():
        c.execute("UPDATE milestones SET achieved=1, achieved_at=? WHERE milestone_id=?", (now_iso(), m["milestone_id"]))
        result["milestones_achieved"].append(m["title"])
    if cur >= g["target_value"] and g["status"] == "ACTIVE":
        c.execute("UPDATE goals SET status='COMPLETED' WHERE goal_id=?", (goal_id,))
        result["goal_completed"] = True
    return result


def apply_practice(c, user_id: str, skill_id: str, minutes: int) -> dict:
    """Add a session's time to every ACTIVE goal of that skill (unit: hours/minutes/sessions)."""
    summary = {"milestones_achieved": [], "goals_completed": []}
    goals = c.execute("SELECT * FROM goals WHERE user_id=? AND skill_id=? AND status='ACTIVE'", (user_id, skill_id)).fetchall()
    for g in goals:
        inc = {"hours": minutes / 60, "minutes": minutes, "sessions": 1}.get(g["unit"].lower(), 0)
        if not inc:
            continue
        c.execute("UPDATE goals SET current_value=? WHERE goal_id=?", (round(g["current_value"] + inc, 4), g["goal_id"]))
        r = refresh_goal(c, g["goal_id"])
        summary["milestones_achieved"] += r["milestones_achieved"]
        if r["goal_completed"]:
            summary["goals_completed"].append(g["title"])
    return summary


def goal_with_progress(c, g) -> dict:
    d = dict(g)
    d["progress_pct"] = progress_pct(g["current_value"], g["target_value"])
    d["milestones"] = [dict(m) for m in c.execute(
        "SELECT milestone_id,title,target_value,achieved,achieved_at FROM milestones WHERE goal_id=? "
        "ORDER BY target_value", (g["goal_id"],)).fetchall()]
    return d

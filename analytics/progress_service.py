"""Progress and analytics calculations. Pure functions (easy to unit test) + one SQL-backed dashboard builder."""
from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable, Optional, Tuple


def progress_pct(current: float, target: float) -> float:
    """Progress % = current / target * 100, capped at 100 for display."""
    if not target or target <= 0:
        return 0.0
    return round(min(100.0, max(0.0, current / target * 100)), 1)


def compute_streaks(days: Iterable[date], today: Optional[date] = None) -> Tuple[int, int]:
    """Return (current_streak, longest_streak) in consecutive calendar days.

    Several sessions on one day count once. The current streak is still alive if you practiced
    today OR yesterday (you have until the end of today to continue it).
    """
    unique = sorted(set(days))
    longest = run = 0
    prev = None
    for d in unique:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    today = today or date.today()
    present = set(unique)
    cursor = today if today in present else today - timedelta(days=1)
    current = 0
    while cursor in present:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def _hours(minutes) -> float:
    return round((minutes or 0) / 60, 2)


def build_dashboard(c, user_id: str, today: Optional[date] = None) -> dict:
    today = today or date.today()
    sessions = c.execute("SELECT s.duration_minutes m, s.practiced_at d, k.skill_name n FROM practice_sessions s "
                         "JOIN skills k ON k.skill_id=s.skill_id WHERE s.user_id=?", (user_id,)).fetchall()
    by_skill, by_day = defaultdict(int), defaultdict(int)
    total = 0
    for r in sessions:
        by_skill[r["n"]] += r["m"]
        by_day[date.fromisoformat(r["d"])] += r["m"]
        total += r["m"]

    week_start = today - timedelta(days=6)
    weekly = sum(m for d, m in by_day.items() if week_start <= d <= today)
    monthly = sum(m for d, m in by_day.items() if d.year == today.year and d.month == today.month)
    current, longest = compute_streaks(by_day.keys(), today)

    # weekly trend: last 8 weeks (Monday-based)
    monday = today - timedelta(days=today.weekday())
    weekly_trend = []
    for i in range(7, -1, -1):
        start = monday - timedelta(weeks=i)
        mins = sum(m for d, m in by_day.items() if start <= d < start + timedelta(days=7))
        weekly_trend.append({"week_start": start.isoformat(), "hours": _hours(mins)})
    # monthly progress: last 6 months
    monthly_progress = []
    y, mth = today.year, today.month
    months = []
    for _ in range(6):
        months.append((y, mth))
        mth -= 1
        if mth == 0:
            y, mth = y - 1, 12
    for (yy, mm) in reversed(months):
        mins = sum(m for d, m in by_day.items() if d.year == yy and d.month == mm)
        monthly_progress.append({"month": f"{yy}-{mm:02d}", "hours": _hours(mins)})

    one = lambda sql, *a: c.execute(sql, a).fetchone()[0]
    goals = c.execute("SELECT title, target_value, current_value, status FROM goals WHERE user_id=?", (user_id,)).fetchall()
    dist = c.execute("SELECT category, COUNT(*) n FROM skills WHERE user_id=? GROUP BY category", (user_id,)).fetchall()
    recent = c.execute("SELECT s.practiced_at, s.duration_minutes, s.activity, k.skill_name FROM practice_sessions s "
                       "JOIN skills k ON k.skill_id=s.skill_id WHERE s.user_id=? "
                       "ORDER BY s.practiced_at DESC, s.created_at DESC LIMIT 5", (user_id,)).fetchall()
    top = max(by_skill.items(), key=lambda kv: kv[1])[0] if by_skill else None
    return {
        "active_skills": one("SELECT COUNT(*) FROM skills WHERE user_id=? AND status='ACTIVE'", user_id),
        "total_practice_hours": _hours(total),
        "weekly_hours": _hours(weekly),
        "monthly_hours": _hours(monthly),
        "most_practiced_skill": top,
        "current_streak": current,
        "longest_streak": longest,
        "goals_completed": sum(1 for g in goals if g["status"] == "COMPLETED"),
        "active_goals": sum(1 for g in goals if g["status"] == "ACTIVE"),
        "milestones_achieved": one("SELECT COUNT(*) FROM milestones m JOIN goals g ON g.goal_id=m.goal_id "
                                   "WHERE g.user_id=? AND m.achieved=1", user_id),
        "posts": one("SELECT COUNT(*) FROM posts WHERE user_id=?", user_id),
        "likes_received": one("SELECT COUNT(*) FROM likes l JOIN posts p ON p.post_id=l.post_id WHERE p.user_id=?", user_id),
        "comments_received": one("SELECT COUNT(*) FROM comments cm JOIN posts p ON p.post_id=cm.post_id "
                                 "WHERE p.user_id=? AND cm.user_id<>?", user_id, user_id),
        "hours_by_skill": sorted(({"skill": k, "hours": _hours(v)} for k, v in by_skill.items()),
                                 key=lambda x: -x["hours"]),
        "weekly_trend": weekly_trend,
        "monthly_progress": monthly_progress,
        "goal_completion": [{"title": g["title"], "progress_pct": progress_pct(g["current_value"], g["target_value"])}
                            for g in goals],
        "skill_distribution": [{"category": r["category"], "count": r["n"]} for r in dist],
        "recent_activity": [dict(r) for r in recent],
    }

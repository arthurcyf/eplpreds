from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy import text
from datetime import date, timedelta
from .. import db
from ..util import window_for

bp = Blueprint("leaderboard", __name__)

def _require_member(s, group_id: int, user_id: int):
    return bool(s.execute(text("""
        select 1 from group_members 
        where group_id=:g and user_id=:u and status='approved'
    """), {"g": group_id, "u": user_id}).first())

@bp.get("/groups/<int:group_id>/leaderboard")
@login_required
def leaderboard(group_id):
    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error":"not in group"}, 403

        rows = s.execute(text("""
          select ws.user_id, sum(ws.points) as total_points, u.username, u.email
          from weekly_scores ws
          join group_members gm on gm.group_id=ws.group_id and gm.user_id=ws.user_id and gm.status='approved'
          join users u on u.id=ws.user_id
          where ws.group_id = :g
          group by ws.user_id, u.username, u.email
          order by total_points desc, ws.user_id asc
        """), {"g": group_id}).mappings().all()
    return {"leaderboard": [dict(r) for r in rows]}

@bp.get("/groups/<int:group_id>/leaderboard/highlights")
@login_required
def highlights(group_id):
    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error":"not in group"}, 403

        # last week's start based on Thu→Wed windows
        this_start, _ = window_for(date.today())
        last_start = this_start - timedelta(days=7)

        rows = s.execute(text("""
          select user_id, points
          from weekly_scores
          where group_id=:g and week_start=:ws
          order by points desc
        """), {"g": group_id, "ws": last_start}).mappings().all()

    if not rows:
        return {"week_start": last_start.isoformat(), "best": None, "worst": None}
    best = rows[0]
    worst = rows[-1]
    return {"week_start": last_start.isoformat(), "best": dict(best), "worst": dict(worst)}

@bp.get("/groups/<int:group_id>/leaderboard/topweeks")
@login_required
def top_weeks_for_user(group_id):
    user_id = request.args.get("user_id", type=int) or current_user.id
    limit = request.args.get("limit", type=int, default=3)

    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error":"not in group"}, 403

        rows = s.execute(text("""
          select week_start, points
          from weekly_scores
          where group_id=:g and user_id=:u
          order by points desc, week_start desc
          limit :n
        """), {"g": group_id, "u": user_id, "n": limit}).mappings().all()
    return {"user_id": user_id, "top_weeks": [dict(r) for r in rows]}
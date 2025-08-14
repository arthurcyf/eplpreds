from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text, select
from datetime import date, timedelta
from .. import db
from ..models import Group
from ..util import window_for

bp = Blueprint("leaderboard", __name__)

@bp.get("/groups/<int:group_id>/leaderboard")
@login_required
def leaderboard(group_id):
    with db.SessionLocal() as s:
        rows = s.execute(text("""
          select user_id, sum(points) as total_points
          from weekly_scores
          where group_id=:g
          group by user_id
          order by total_points desc
        """), {"g": group_id}).mappings().all()
    return {"leaderboard": [dict(r) for r in rows]}

@bp.get("/groups/<int:group_id>/leaderboard/highlights")
@login_required
def highlights(group_id):
    # last week's start based on Thu→Wed windows
    this_start, _ = window_for(date.today())
    last_start = this_start - timedelta(days=7)
    with db.SessionLocal() as s:
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
        rows = s.execute(text("""
          select week_start, points
          from weekly_scores
          where group_id=:g and user_id=:u
          order by points desc, week_start desc
          limit :n
        """), {"g": group_id, "u": user_id, "n": limit}).mappings().all()
    return {"user_id": user_id, "top_weeks": [dict(r) for r in rows]}
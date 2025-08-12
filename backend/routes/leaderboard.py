from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text
from .. import db

bp = Blueprint("leaderboard", __name__)

@bp.get("/groups/<int:group_id>/leaderboard")
@login_required
def leaderboard(group_id):
    # cumulative points up to last Thursday
    with db.SessionLocal() as s:
        rows = s.execute(text("""
          select user_id, sum(points) as total_points
          from weekly_scores
          where group_id=:g
          group by user_id
          order by total_points desc
        """), {"g": group_id}).mappings().all()
    return jsonify({"leaderboard": [dict(r) for r in rows]})
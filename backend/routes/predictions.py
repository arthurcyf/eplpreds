from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import select, text
from datetime import date, timedelta, datetime, timezone
from .. import db
from ..models import Prediction, Match, GroupMember
from ..util import window_for

bp = Blueprint("preds", __name__)

def windows(today: date):
    cur_s, cur_e = window_for(today)                # Thu→Wed containing `today`
    next_s = cur_s + timedelta(days=7)
    next_e = next_s + timedelta(days=6)
    return (cur_s, cur_e), (next_s, next_e)

@bp.get("/groups/<int:group_id>/predictions/window")
@login_required
def current_window(group_id):
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    return {
        "current": {"start": cur_s.isoformat(), "end": cur_e.isoformat(), "open": date.today() >= cur_s},
        "next":    {"start": next_s.isoformat(), "end": next_e.isoformat(), "open": date.today() >= next_s},
    }

@bp.get("/groups/<int:group_id>/predictions/matches")
@login_required
def matches_for_week(group_id):
    # membership check
    with db.SessionLocal() as s:
        m = s.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id
            )
        ).scalar_one_or_none()
        if not m:
            return {"error": "not in group"}, 403

    scope = (request.args.get("scope") or "current").lower()
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    start, end = (cur_s, cur_e) if scope == "current" else (next_s, next_e)

    with db.SessionLocal() as s:
        rows = s.execute(text("""
          select match_id, date, time, home, away
          from matches
          where date between :a and :b
          order by date, time
        """), {"a": start, "b": end}).mappings().all()

    return {"scope": scope, "week_start": start.isoformat(), "matches": [dict(r) for r in rows]}

@bp.post("/groups/<int:group_id>/predictions")
@login_required
def submit_predictions(group_id):
    body = request.get_json(silent=True) or {}
    entries = body.get("predictions", [])
    if not entries:
        return {"error": "no predictions"}, 400

    scope = (request.args.get("scope") or "current").lower()
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    start, end = (cur_s, cur_e) if scope == "current" else (next_s, next_e)

    # Only allow submissions once the window is open (Thursday 00:00 local)
    if date.today() < start:
        return {"error": f"predictions for this window open on {start.isoformat()}"}, 403

    saved = 0
    with db.SessionLocal() as s:
        # membership check
        m = s.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id
            )
        ).scalar_one_or_none()
        if not m:
            return {"error": "not in group"}, 403

        for e in entries:
            mid = int(e["match_id"])
            hm = int(e["home_pred"])
            aw = int(e["away_pred"])

            match = s.get(Match, mid)
            if not match:
                continue
            if not (start <= match.date <= end):
                continue
            # lock at kickoff
            if datetime.now(timezone.utc) >= match.utc_kickoff:
                continue

            s.execute(text("""
              insert into predictions (group_id,user_id,match_id,home_pred,away_pred,created_at,updated_at)
              values (:g,:u,:m,:hp,:ap, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
              on conflict (group_id,user_id,match_id) do update set
                home_pred=excluded.home_pred,
                away_pred=excluded.away_pred,
                updated_at=CURRENT_TIMESTAMP
            """), {"g": group_id, "u": current_user.id, "m": mid, "hp": hm, "ap": aw})
            saved += 1
        s.commit()

    return {"ok": True, "saved": saved, "scope": scope, "week_start": start.isoformat()}
from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, text
from datetime import date, timedelta, datetime, timezone, time
from .. import db
from ..models import Prediction, Match, GroupMember, User
from ..util import window_for

bp = Blueprint("preds", __name__)

# -------- Window helpers --------

def windows(today: date):
    cur_s, cur_e = window_for(today)                # Thu→Wed containing `today`
    next_s = cur_s + timedelta(days=7)
    next_e = next_s + timedelta(days=6)
    return (cur_s, cur_e), (next_s, next_e)

def _open_close_times_local(anchor_day: date):
    """
    Open at Thu 09:00 LOCAL; close 2h before the FIRST match in that Thu→Wed window.
    """
    start, end = window_for(anchor_day)

    # Open (local): Thu 09:00
    tz = getattr(current_app, "LOCAL_TZ", None)  # attach ZoneInfo to app in create_app() if you want local tz
    open_at = datetime.combine(start, time(9, 0))
    if tz:
        open_at = open_at.replace(tzinfo=tz)

    # Close: 2h before first local_kickoff in the window (fallback to open_at if no games)
    with db.SessionLocal() as s:
        first_kick = s.execute(text("""
            select min(local_kickoff) as first_local
            from matches
            where date between :a and :b
        """), {"a": start, "b": end}).scalar()
    close_at = (first_kick - timedelta(hours=2)) if first_kick else open_at
    return start, end, open_at, close_at

def _is_open_now_for_current():
    start, end, open_at, close_at = _open_close_times_local(date.today())
    now = datetime.now(open_at.tzinfo) if open_at.tzinfo else datetime.now()
    return (open_at <= now < close_at), start, end, open_at, close_at

def _require_member(s, group_id: int, user_id: int):
    return bool(s.execute(
        select(GroupMember).where(
            GroupMember.group_id==group_id,
            GroupMember.user_id==user_id,
            GroupMember.status=="approved",
        )
    ).scalar_one_or_none())

# -------- Endpoints --------

@bp.get("/groups/<int:group_id>/predictions/window")
@login_required
def current_window(group_id):
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    _, _, cur_open, cur_close = _open_close_times_local(date.today())
    _, _, nxt_open, nxt_close = _open_close_times_local(next_s)
    now = datetime.now(cur_open.tzinfo) if cur_open.tzinfo else datetime.now()
    return {
        "current": {"start": cur_s.isoformat(), "end": cur_e.isoformat(),
                    "open_at": cur_open.isoformat(), "close_at": cur_close.isoformat(),
                    "open": (cur_open <= now < cur_close)},
        "next": {"start": next_s.isoformat(), "end": next_e.isoformat(),
                 "open_at": nxt_open.isoformat(), "close_at": nxt_close.isoformat(),
                 "open": (nxt_open <= now < nxt_close)},
    }

@bp.get("/groups/<int:group_id>/predictions/matches")
@login_required
def matches_for_predictions(group_id):
    """
    List matches in the current/next window and include *my* latest saved picks
    as `my_home_pred` / `my_away_pred`. Dates are returned as YYYY-MM-DD (no time).
    """
    scope = (request.args.get("scope") or "current").lower()
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    start, end = (cur_s, cur_e) if scope == "current" else (next_s, next_e)

    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error": "not in group"}, 403

        rows = s.execute(text("""
          select m.match_id, m.date, m.home, m.away,
                 p.home_pred as my_home_pred, p.away_pred as my_away_pred
          from matches m
          left join predictions p
            on p.group_id=:g and p.user_id=:u and p.match_id=m.match_id
          where m.date between :a and :b
          order by m.date asc, m.match_id asc
        """), {"g": group_id, "u": current_user.id, "a": start, "b": end}).mappings().all()

    # ensure date-only strings
    matches = []
    for r in rows:
        d = dict(r)
        # cast date to ISO YYYY-MM-DD; avoid adding any time fields
        d["date"] = (d["date"].isoformat() if hasattr(d["date"], "isoformat") else str(d["date"]))
        matches.append(d)

    return {"scope": scope, "week_start": start.isoformat(), "matches": matches}

@bp.post("/groups/<int:group_id>/predictions")
@login_required
def submit_predictions(group_id):
    """
    Save (upsert) user's predictions for matches in the selected window.
    Enforces window open/close and per-match kickoff lock (UTC).
    """
    body = request.get_json(silent=True) or {}
    entries = body.get("predictions", [])
    if not entries:
        return {"error": "no predictions"}, 400

    scope = (request.args.get("scope") or "current").lower()
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    start, end = (cur_s, cur_e) if scope == "current" else (next_s, next_e)

    # Window open/close check
    is_open, _, _, open_at, close_at = _is_open_now_for_current()
    if scope == "next":
        _, _, open_at, close_at = _open_close_times_local(next_s)
        now = datetime.now(open_at.tzinfo) if open_at.tzinfo else datetime.now()
        is_open = (open_at <= now < close_at)

    allow_early_qs = request.args.get("allow_early") == "1"
    allow_early_cfg = bool(current_app.config.get("DEV_PRED_BYPASS"))
    if not (is_open or allow_early_qs or allow_early_cfg):
        return {"error": f"predictions open {open_at} and close {close_at} (local time)"}, 403

    saved = 0
    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error": "not in group"}, 403

        for e in entries:
            try:
                mid = int(e["match_id"])
                hm = int(e["home_pred"])
                aw = int(e["away_pred"])
            except Exception:
                continue

            match = s.get(Match, mid)
            if not match:
                continue
            if not (start <= match.date <= end):
                continue
            # Lock per match at kickoff (UTC)
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

@bp.get("/groups/<int:group_id>/predictions/others")
@login_required
def others_submitted(group_id):
    """
    Show other members' submitted predictions immediately (no need to wait until window closes).
    """
    scope = (request.args.get("scope") or "current").lower()
    (cur_s, cur_e), (next_s, next_e) = windows(date.today())
    start, end = (cur_s, cur_e) if scope == "current" else (next_s, next_e)

    with db.SessionLocal() as s:
        if not _require_member(s, group_id, current_user.id):
            return {"error": "not in group"}, 403

        rows = s.execute(text("""
          select p.match_id, m.home, m.away, u.username, u.email, p.home_pred, p.away_pred, p.updated_at
          from predictions p
          join matches m on m.match_id=p.match_id
          join users u on u.id=p.user_id
          where p.group_id=:g and m.date between :a and :b
          order by p.updated_at desc
        """), {"g": group_id, "a": start, "b": end}).mappings().all()

    items = [dict(r) for r in rows]
    # no times returned except updated_at (useful for ordering/debug)
    return {"scope": scope, "week_start": start.isoformat(), "predictions": items}

@bp.get("/groups/<int:group_id>/predictions/stats")
@login_required
def prediction_stats(group_id):
    """
    Aggregate stats (outcomes and exact score frequencies).
    Kept gated until the *current* window closes to avoid influencing picks.
    """
    is_open, start, end, open_at, close_at = _is_open_now_for_current()
    now = datetime.now(close_at.tzinfo) if close_at.tzinfo else datetime.now()
    if now < close_at:
        return {"error": "stats available after window closes", "close_at": close_at.isoformat()}, 403

    with db.SessionLocal() as s:
        # (Optional) you can require membership here too, but these are group-bound stats
        outcome_rows = s.execute(text("""
          with picks as (
            select p.match_id,
                   case when p.home_pred > p.away_pred then 'home'
                        when p.home_pred = p.away_pred then 'draw'
                        else 'away' end as outcome
            from predictions p
            join matches m on m.match_id = p.match_id
            where p.group_id=:g and m.date between :a and :b
          )
          select match_id, outcome, count(*) as c
          from picks
          group by match_id, outcome
          order by match_id
        """), {"g": group_id, "a": start, "b": end}).mappings().all()

        score_rows = s.execute(text("""
          select p.match_id, concat(p.home_pred,'-',p.away_pred) as score, count(*) as c
          from predictions p
          join matches m on m.match_id = p.match_id
          where p.group_id=:g and m.date between :a and :b
          group by p.match_id, score
          order by p.match_id
        """), {"g": group_id, "a": start, "b": end}).mappings().all()

        labels = s.execute(text("""
          select match_id, home, away from matches where date between :a and :b
        """), {"a": start, "b": end}).mappings().all()

    by_match = {
        r["match_id"]: {
            "match_id": r["match_id"],
            "home": r["home"],
            "away": r["away"],
            "outcomes": {"home": 0, "draw": 0, "away": 0},
            "scores": []
        } for r in labels
    }
    for r in outcome_rows:
        by_match[r["match_id"]]["outcomes"][r["outcome"]] = r["c"]
    for r in score_rows:
        by_match[r["match_id"]]["scores"].append({"score": r["score"], "count": r["c"]})

    return {"week_start": start.isoformat(), "matches": list(by_match.values())}
from sqlalchemy import text
from datetime import date
from . import db
from .util import window_for, points_for

def recompute_week(group_id: int, week_start: date):
    # Pull predictions + final scores for the week, compute & upsert weekly_scores
    with db.SessionLocal() as s:
        rows = s.execute(text("""
          select p.user_id, p.group_id, p.match_id, p.home_pred, p.away_pred,
                 m.home_score, m.away_score
          from predictions p
          join matches m on m.match_id = p.match_id
          where p.group_id=:g and m.date between :a and :b
        """), {"g": group_id, "a": week_start, "b": week_start.fromordinal(week_start.toordinal()+6)}).mappings().all()

        totals = {}
        for r in rows:
            pts = points_for(r["home_pred"], r["away_pred"], r["home_score"], r["away_score"])
            totals[r["user_id"]] = totals.get(r["user_id"], 0) + pts

        for uid, pts in totals.items():
            s.execute(text("""
              insert into weekly_scores (group_id,user_id,week_start,points,updated_at)
              values (:g,:u,:ws,:p, CURRENT_TIMESTAMP)
              on conflict (group_id,user_id,week_start) do update set
                points=excluded.points, updated_at=CURRENT_TIMESTAMP
            """), {"g":group_id,"u":uid,"ws":week_start, "p":pts})
        s.commit()

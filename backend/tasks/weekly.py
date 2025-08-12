from datetime import datetime, timezone, date, timedelta
from sqlalchemy import text
from .. import db
from ..config import Config
from ..services.football_data import to_local_from_utc_iso, fetch_matches
from zoneinfo import ZoneInfo
from sqlalchemy import select
from ..models import Group
from ..scoring import recompute_week
from ..util import window_for
from datetime import date

cfg = Config.from_env()
LOCAL_TZ = None
try:
    LOCAL_TZ = ZoneInfo(cfg.timezone)
except Exception:
    pass

def iso(d): return d.strftime("%Y-%m-%d")
def next_range(days=7): s = date.today(); e = s + timedelta(days=days); return iso(s), iso(e)
def prev_range(days=7): e = date.today() - timedelta(days=1); s = e - timedelta(days=days-1); return iso(s), iso(e)

UPSERT_SQL = text("""
  insert into matches (
    match_id, status, competition, season, home, away,
    utc_kickoff, local_kickoff, date, time, home_score, away_score, updated_at
  ) values (
    :match_id, :status, 'Premier League', :season, :home, :away,
    :utc_kickoff, :local_kickoff, :date, :time, :home_score, :away_score, :updated_at
  )
  on conflict (match_id) do update set
    status        = excluded.status,
    home_score    = excluded.home_score,
    away_score    = excluded.away_score,
    utc_kickoff   = excluded.utc_kickoff,
    local_kickoff = excluded.local_kickoff,
    date          = excluded.date,
    time          = excluded.time,
    updated_at    = excluded.updated_at
""")

def upsert_matches(matches, season_label=cfg.season_label):
    rows, now_ts = [], datetime.now(timezone.utc)
    for m in matches:
        dt_loc, d_str, t_str = to_local_from_utc_iso(m["utcDate"], LOCAL_TZ)
        full = (m.get("score") or {}).get("fullTime") or {}
        rows.append({
            "match_id": m["id"],
            "status": m.get("status") or "",
            "season": season_label,
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "utc_kickoff": datetime.fromisoformat(m["utcDate"].replace("Z","+00:00")),
            "local_kickoff": dt_loc,
            "date": d_str,
            "time": t_str,
            "home_score": full.get("home"),
            "away_score": full.get("away"),
            "updated_at": now_ts,
        })
    if not rows: return 0
    with db.SessionLocal() as s:
        s.execute(UPSERT_SQL, rows)
        s.commit()
    return len(rows)

def run_weekly_job():
    f_start, f_end = next_range(7)
    r_start, r_end = prev_range(7)
    fxs = fetch_matches(cfg.pl_code, cfg.fd_token, f_start, f_end, "SCHEDULED")
    rsl = fetch_matches(cfg.pl_code, cfg.fd_token, r_start, r_end, "FINISHED")
    n1 = upsert_matches(fxs); n2 = upsert_matches(rsl)
    result = {"fixtures_upserted": n1, "results_upserted": n2}  # <- your actual counts

    # scoring: recompute for all groups for the week that just ended
    ws, _ = window_for(date.today())         # current week
    last_week_start = ws.fromordinal(ws.toordinal()-7)
    with db.SessionLocal() as s:
        groups = s.execute(select(Group)).scalars().all()
    for g in groups:
        recompute_week(g.id, last_week_start)

    return result

# app.py
import os, requests, traceback
from datetime import datetime, timezone, timedelta, date
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from sqlalchemy import create_engine, text, Column, Integer, BigInteger, String, DateTime, Date
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------ env & app ------------------
load_dotenv(override=True)
app = Flask(__name__)

# ------------------ DB setup -------------------
db_url = os.getenv("DATABASE_URL", "sqlite:///epl.db")

# normalize to psycopg v3 if using Postgres URLs
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(db_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    match_id      = Column(BigInteger, primary_key=True)
    status        = Column(String(20))
    competition   = Column(String(40), default="Premier League", nullable=False)
    season        = Column(String(12), nullable=False)
    home          = Column(String(100), nullable=False)
    away          = Column(String(100), nullable=False)
    utc_kickoff   = Column(DateTime(timezone=True), nullable=False)
    local_kickoff = Column(DateTime(timezone=True), nullable=False)
    date          = Column(Date, nullable=False)      # local date
    time          = Column(String(5), nullable=False) # local HH:MM
    home_score    = Column(Integer)
    away_score    = Column(Integer)
    updated_at    = Column(DateTime(timezone=True), nullable=False)

Base.metadata.create_all(engine)

# ------------------ football-data.org -------------------
FD_TOKEN = os.getenv("FOOTBALL_DATA_API_KEY")
if not FD_TOKEN:
    raise RuntimeError("FOOTBALL_DATA_API_KEY missing in .env")

HEADERS = {"X-Auth-Token": FD_TOKEN}
FD_BASE = "https://api.football-data.org/v4"
PL_CODE = "PL"  # Premier League

# ------------------ timezone -------------------
TZ_NAME = os.getenv("TIMEZONE", "Asia/Singapore")
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo(TZ_NAME)
except Exception:
    LOCAL_TZ = None  # fallback to UTC if tz db missing on Windows (pip install tzdata)

def to_local_from_utc_iso(utc_iso: str):
    """Return local datetime + ('YYYY-MM-DD','HH:MM') from a football-data utcDate."""
    dt_utc = datetime.fromisoformat(utc_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    dt_loc = dt_utc.astimezone(LOCAL_TZ) if LOCAL_TZ else dt_utc
    return dt_loc, dt_loc.strftime("%Y-%m-%d"), dt_loc.strftime("%H:%M")

def _to_local(utc_iso: str):
    _, d, t = to_local_from_utc_iso(utc_iso)
    return d, t

# ------------------ date helpers -------------------
def iso(d): return d.strftime("%Y-%m-%d")
def next_range(days=7):
    s = date.today(); e = s + timedelta(days=days); return iso(s), iso(e)
def prev_range(days=7):
    e = date.today() - timedelta(days=1); s = e - timedelta(days=days-1); return iso(s), iso(e)

# ------------------ FD.org calls -------------------
def fd_matches(date_from, date_to, status):
    params = {"dateFrom": date_from, "dateTo": date_to}
    if status:
        params["status"] = status  # SCHEDULED or FINISHED
    url = f"{FD_BASE}/competitions/{PL_CODE}/matches"
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("errorCode"):
        raise RuntimeError(f"FD error: {data.get('message')}")
    return data.get("matches", [])

def normalize(matches):
    out = []
    for m in matches:
        d, t = _to_local(m["utcDate"])
        out.append({
            "date": d,
            "time": t,
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "competition": "Premier League",
            "season": "2025/26",
        })
    return out

# ------------------ Upsert into DB -------------------
def upsert_matches(fd_ms, season_label="2025/26"):
    """
    Postgres/SQLite-friendly upsert. We pass updated_at from Python so we avoid DB-specific NOW() syntax.
    """
    sql = text("""
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
    rows = []
    now_ts = datetime.now(timezone.utc)
    for m in fd_ms:
        dt_loc, d_str, t_str = to_local_from_utc_iso(m["utcDate"])
        full = (m.get("score") or {}).get("fullTime") or {}
        rows.append({
            "match_id": m["id"],
            "status": m.get("status") or "",
            "season": season_label,
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "utc_kickoff": datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
            "local_kickoff": dt_loc,
            "date": d_str,
            "time": t_str,
            "home_score": full.get("home"),
            "away_score": full.get("away"),
            "updated_at": now_ts,
        })
    with SessionLocal() as s:
        if rows:
            s.execute(sql, rows)  # executes many
            s.commit()
    return len(rows)

# ------------------ endpoints -------------------
@app.get("/api/db/fixtures")
def db_fixtures():
    start = request.args.get("from"); end = request.args.get("to")
    q = text("""
      select date, time, home, away, competition, season
      from matches
      where date between :a and :b
        and status not in ('FT','AET','PEN')
      order by date, time
    """)
    with SessionLocal() as s:
        rows = s.execute(q, {"a": start, "b": end}).mappings().all()
    return jsonify({"success": True, "fixtures": [dict(r) for r in rows]})

@app.get("/api/fixtures")
def fixtures():
    days = int(request.args.get("days", 7))
    start = request.args.get("from"); end = request.args.get("to")
    if not start or not end: start, end = next_range(days)
    matches = fd_matches(start, end, status="SCHEDULED")
    return jsonify({"success": True, "fixtures": normalize(matches)})

@app.get("/api/results")
def results():
    days = int(request.args.get("days", 7))
    start = request.args.get("from"); end = request.args.get("to")
    if not start or not end: start, end = prev_range(days)
    matches = fd_matches(start, end, status="FINISHED")
    return jsonify({"success": True, "results": normalize(matches)})

@app.get("/health")
def health():
    return {"ok": True, "db": db_url.split("://", 1)[0], "tz": TZ_NAME}

# -------- optional: upsert by calling live API (manual) --------
@app.post("/admin/run-scrape")
def run_scrape_now():
    f_start, f_end = next_range(7)
    r_start, r_end = prev_range(7)
    fixtures = fd_matches(f_start, f_end, status="SCHEDULED")
    results  = fd_matches(r_start, r_end, status="FINISHED")
    n1 = upsert_matches(fixtures)
    n2 = upsert_matches(results)
    return {"ok": True, "inserted_or_updated": {"fixtures": n1, "results": n2}}

# ------------------ error handler -------------------
@app.errorhandler(Exception)
def handle_any_error(e):
    traceback.print_exc()
    return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)), debug=True)
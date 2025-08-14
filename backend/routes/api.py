from flask import Blueprint, request, jsonify, current_app
from datetime import date, timedelta, timezone, datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from requests import HTTPError

from ..config import Config
from ..services.football_data import fetch_matches, to_local_from_utc_iso
from .. import db

bp = Blueprint("api", __name__)
cfg = Config.from_env()

try:
    LOCAL_TZ = ZoneInfo(cfg.timezone)
except Exception:
    LOCAL_TZ = None

def iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def next_range(days=7):
    s = date.today()
    e = s + timedelta(days=days)
    return iso(s), iso(e)

def prev_range(days=7):
    e = date.today() - timedelta(days=1)
    s = e - timedelta(days=days - 1)
    return iso(s), iso(e)

# ---------- Helpers ----------

def _upsert_matches_from_api(api_items, finished: bool):
    """
    Map football-data API objects into our schema and upsert into `matches`.
    - finished=True  -> status 'FT' and includes scores
    - finished=False -> status 'SCHEDULED' and scores null
    """
    season_label = getattr(cfg, "season_label", None)

    with db.SessionLocal() as s:
        for m in api_items:
            # API fields
            utc_iso = m.get("utcDate")
            home = (m.get("homeTeam") or {}).get("name")
            away = (m.get("awayTeam") or {}).get("name")

            # Convert to local + date/time strings for our columns
            dt_loc, d_str, t_str = to_local_from_utc_iso(utc_iso, LOCAL_TZ) if utc_iso else (None, None, None)

            # Scores (only for finished)
            ft = (m.get("score") or {}).get("fullTime") or {}
            home_score = ft.get("home") if finished else None
            away_score = ft.get("away") if finished else None

            # Timestamps for utc/local kickoff
            utc_ts = None
            try:
                if utc_iso:
                    utc_ts = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
            except Exception:
                utc_ts = None

            s.execute(
                text(
                    """
                    INSERT INTO matches
                      (match_id, status, competition, season,
                       home, away, utc_kickoff, local_kickoff,
                       date, time, home_score, away_score, updated_at)
                    VALUES
                      (:id, :status, :competition, :season,
                       :home, :away, :utc_kickoff, :local_kickoff,
                       :date, :time, :hs, :as, now())
                    ON CONFLICT (match_id) DO UPDATE SET
                      status        = EXCLUDED.status,
                      competition   = EXCLUDED.competition,
                      season        = EXCLUDED.season,
                      home          = EXCLUDED.home,
                      away          = EXCLUDED.away,
                      utc_kickoff   = EXCLUDED.utc_kickoff,
                      local_kickoff = EXCLUDED.local_kickoff,
                      date          = EXCLUDED.date,
                      time          = EXCLUDED.time,
                      home_score    = EXCLUDED.home_score,
                      away_score    = EXCLUDED.away_score,
                      updated_at    = now()
                    """
                ),
                {
                    "id": m.get("id"),
                    "status": "FT" if finished else "SCHEDULED",
                    "competition": "Premier League",
                    "season": season_label,
                    "home": home,
                    "away": away,
                    "utc_kickoff": utc_ts,
                    "local_kickoff": utc_ts,  # convert to real local tz if you prefer
                    "date": d_str,
                    "time": t_str,            # <— store time string
                    "hs": home_score,
                    "as": away_score,
                },
            )
        s.commit()

def _db_results(a: date, b: date):
    """Finished matches from DB; include time field for the frontend to ignore/show."""
    with db.SessionLocal() as s:
        rows = s.execute(
            text(
                """
                SELECT match_id, date, time, home, away, home_score, away_score, status
                FROM matches
                WHERE date BETWEEN :a AND :b
                  AND (
                        status IN ('FT','FINISHED','AET','PEN')
                     OR (home_score IS NOT NULL AND away_score IS NOT NULL)
                  )
                ORDER BY date DESC, match_id DESC
                """
            ),
            {"a": a, "b": b},
        ).mappings().all()
    return [
        {
            "match_id": r["match_id"],
            "date": r["date"].isoformat() if hasattr(r["date"], "isoformat") else str(r["date"]),
            "time": r["time"],  # <— included
            "home": r["home"],
            "away": r["away"],
            "home_score": r["home_score"],
            "away_score": r["away_score"],
        }
        for r in rows
    ]

def _db_upcoming(now_utc: datetime, limit: int):
    """Upcoming matches from DB; include time field."""
    with db.SessionLocal() as s:
        rows = s.execute(
            text(
                """
                SELECT match_id, date, time, home, away
                FROM matches
                WHERE (status IS NULL OR status NOT IN ('FT','AET','PEN','FINISHED'))
                  AND utc_kickoff > :now_utc
                ORDER BY utc_kickoff ASC
                LIMIT :n
                """
            ),
            {"now_utc": now_utc, "n": limit},
        ).mappings().all()
    return [
        {
            "match_id": r["match_id"],
            "date": r["date"].isoformat() if hasattr(r["date"], "isoformat") else str(r["date"]),
            "time": r["time"],  # <— included
            "home": r["home"],
            "away": r["away"],
        }
        for r in rows
    ]

# ---------- Routes ----------

@bp.get("/health")
def health():
    return {"ok": True, "tz": cfg.timezone}

@bp.get("/fixtures")
def fixtures():
    # API-only (not cached) — unchanged
    days = int(request.args.get("days", 7))
    start = request.args.get("from")
    end = request.args.get("to")
    if not start or not end:
        start, end = next_range(days)
    matches = fetch_matches(cfg.pl_code, cfg.fd_token, start, end, "SCHEDULED")
    out = []
    for m in matches:
        dt_loc, d, t = to_local_from_utc_iso(m["utcDate"], LOCAL_TZ)
        out.append(
            {
                "date": d,
                "time": t,
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "competition": "Premier League",
                "season": cfg.season_label,
            }
        )
    return jsonify({"success": True, "fixtures": out})

@bp.get("/results")
def results():
    """
    DB-first finished matches.
    If DB empty or you force `?source=api`, fetch from API, upsert into DB, then return.
    Returns date **and** time; the frontend can choose to hide the time.
    """
    days = int(request.args.get("days", 7))
    start_q = request.args.get("from")
    end_q = request.args.get("to")
    if not start_q or not end_q:
        start_s, end_s = prev_range(days)
    else:
        start_s, end_s = start_q, end_q

    start = datetime.fromisoformat(start_s).date()
    end = datetime.fromisoformat(end_s).date()
    source = (request.args.get("source") or "").lower()  # db | api

    # 1) DB-first (unless forced API)
    if source != "api":
        items = _db_results(start, end)
        if items:
            return jsonify({"success": True, "results": items, "source": "db", "from": start_s, "to": end_s})

    # 2) API fetch (FINISHED) -> upsert -> return DB rows
    try:
        api_matches = fetch_matches(cfg.pl_code, cfg.fd_token, start_s, end_s, "FINISHED")
        _upsert_matches_from_api(api_matches, finished=True)
        items = _db_results(start, end)
        return jsonify({"success": True, "results": items, "source": "api", "from": start_s, "to": end_s})
    except HTTPError:
        # On rate-limit/HTTP errors: fall back to whatever DB has (maybe empty)
        items = _db_results(start, end)
        return jsonify({"success": True, "results": items, "source": "db_fallback", "from": start_s, "to": end_s})
    except Exception:
        items = _db_results(start, end)
        return jsonify({"success": True, "results": items, "source": "db_fallback", "from": start_s, "to": end_s})

@bp.get("/upcoming")
def upcoming():
    """
    DB-first upcoming.
    If DB has fewer than `limit` rows, fetch next `days` window from API (SCHEDULED),
    upsert into DB, then return the first `limit` rows from DB.
    Returns date **and** time; the frontend can choose to hide the time.
    """
    limit = int(request.args.get("limit", 10))
    days = int(request.args.get("days", 7))  # how far ahead to fetch if we need API
    source = "db"

    now_utc = datetime.now(timezone.utc)
    items = _db_upcoming(now_utc, limit)

    if len(items) < limit:
        # Need to top up cache from API
        start_s, end_s = next_range(days)
        try:
            api_matches = fetch_matches(cfg.pl_code, cfg.fd_token, start_s, end_s, "SCHEDULED")
            _upsert_matches_from_api(api_matches, finished=False)
            source = "api"
        except HTTPError:
            source = "db_fallback"
        except Exception:
            source = "db_fallback"
        # Re-read from DB after attempted upsert
        items = _db_upcoming(now_utc, limit)

    return {"items": items, "source": source}
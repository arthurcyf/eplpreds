from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from ..config import Config
from ..services.football_data import fetch_matches, to_local_from_utc_iso

bp = Blueprint("api", __name__)
cfg = Config.from_env()

try:
    LOCAL_TZ = ZoneInfo(cfg.timezone)
except Exception:
    LOCAL_TZ = None

def iso(d): return d.strftime("%Y-%m-%d")
def next_range(days=7): s = date.today(); e = s + timedelta(days=days); return iso(s), iso(e)
def prev_range(days=7): e = date.today() - timedelta(days=1); s = e - timedelta(days=days-1); return iso(s), iso(e)

def normalize(matches):
    out = []
    for m in matches:
        dt_loc, d, t = to_local_from_utc_iso(m["utcDate"], LOCAL_TZ)
        out.append({
            "date": d, "time": t,
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "competition": "Premier League",
            "season": cfg.season_label
        })
    return out

@bp.get("/health")
def health(): return {"ok": True, "tz": cfg.timezone}

@bp.get("/fixtures")
def fixtures():
    days = int(request.args.get("days", 7))
    start = request.args.get("from"); end = request.args.get("to")
    if not start or not end: start, end = next_range(days)
    matches = fetch_matches(cfg.pl_code, cfg.fd_token, start, end, "SCHEDULED")
    return jsonify({"success": True, "fixtures": normalize(matches)})

@bp.get("/results")
def results():
    days = int(request.args.get("days", 7))
    start = request.args.get("from"); end = request.args.get("to")
    if not start or not end: start, end = prev_range(days)
    matches = fetch_matches(cfg.pl_code, cfg.fd_token, start, end, "FINISHED")
    return jsonify({"success": True, "results": normalize(matches)})

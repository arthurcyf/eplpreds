import os, requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

FD_BASE = "https://api.football-data.org/v4"

def to_local_from_utc_iso(utc_iso: str, tz: ZoneInfo | None):
    dt_utc = datetime.fromisoformat(utc_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    if tz: dt_loc = dt_utc.astimezone(tz)
    else:  dt_loc = dt_utc
    return dt_loc, dt_loc.strftime("%Y-%m-%d"), dt_loc.strftime("%H:%M")

def fetch_matches(pl_code: str, token: str, date_from: str, date_to: str, status: str | None):
    params = {"dateFrom": date_from, "dateTo": date_to}
    if status: params["status"] = status
    r = requests.get(f"{FD_BASE}/competitions/{pl_code}/matches",
                     headers={"X-Auth-Token": token}, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("errorCode"):
        raise RuntimeError(f"FD error: {data.get('message')}")
    return data.get("matches", [])

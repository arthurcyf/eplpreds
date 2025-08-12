from flask import Blueprint, jsonify
from ..tasks.weekly import run_weekly_job

bp = Blueprint("admin", __name__)

@bp.post("/admin/run-scrape")
def run_scrape_now():
    result = run_weekly_job()
    return jsonify({"ok": True, **result})

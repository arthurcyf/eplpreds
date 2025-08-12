from flask import Blueprint, jsonify

bp = Blueprint("root", __name__)

@bp.get("/")
def index():
    return jsonify({
        "ok": True,
        "message": "EPL API running",
        "endpoints": {
            "health": "/api/health",
            "fixtures": "/api/fixtures?from=YYYY-MM-DD&to=YYYY-MM-DD",
            "results": "/api/results?from=YYYY-MM-DD&to=YYYY-MM-DD",
            "run_scrape": "POST /admin/run-scrape"
        }
    })

@bp.get("/favicon.ico")
def favicon():
    # no favicon yet; avoid 404 noise
    return ("", 204)
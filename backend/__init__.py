# backend/__init__.py
from flask import Flask
from dotenv import load_dotenv
import os, re
from zoneinfo import ZoneInfo
from flask_cors import CORS

from .config import Config
from .db import init_db, Base
from .models import Match
from .routes import register_blueprints
from .routes.auth import login_manager
# from .scheduler import start_scheduler  # import lazily inside the flag below

__all__ = ["create_app"]

load_dotenv(override=True)

def create_app():
    cfg = Config.from_env()

    app = Flask(__name__)
    app.url_map.strict_slashes = False  # avoid 301/308 on trailing slash during preflight

    # timezone + core config
    app.LOCAL_TZ = ZoneInfo(cfg.timezone or "Asia/Singapore")
    app.config.update(
        DEV_PRED_BYPASS=os.getenv("DEV_PRED_BYPASS", "0") in ("1","true","True"),
        TIMEZONE=cfg.timezone,
        DATABASE_URL=cfg.database_url,
        PORT=cfg.port,
        SEASON_LABEL=cfg.season_label,
        PL_CODE=cfg.pl_code,
        SECRET_KEY=cfg.secret_key,
        # cross-site cookies (Vercel <-> Render)
        SESSION_COOKIE_SECURE=bool(int(os.getenv("SESSION_COOKIE_SECURE", "1"))),
        SESSION_COOKIE_SAMESITE="None",
    )

    # DB init + create tables
    engine, _ = init_db(cfg.database_url)
    Base.metadata.create_all(engine)

    # routes
    login_manager.init_app(app)
    register_blueprints(app)

    # ----- CORS -----
    # Comma-separated exact origins in env; optional wildcard for any *.vercel.app preview
    raw = os.getenv("ALLOWED_ORIGINS", "")
    allowed = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    vercel_wildcard = re.compile(r"^https://.*\.vercel\.app$")  # optional

    CORS(
        app,
        resources={r"/*": {"origins": allowed + [vercel_wildcard]}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["Content-Type"],
        max_age=600,
    )

    # ----- Scheduler (run only in the worker service) -----
    if os.getenv("ENABLE_SCHEDULER") in ("1", "true", "True"):
        from .scheduler import start_scheduler
        start_scheduler(app)

    return app
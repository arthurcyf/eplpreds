# backend/__init__.py
from flask import Flask
from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo
from flask_cors import CORS

from .config import Config
from .db import init_db, Base
from .models import Match  # ensure model is imported so metadata sees it
from .routes import register_blueprints
from .routes.auth import login_manager
# from .scheduler import start_scheduler  # run as a separate worker in production

__all__ = ["create_app"]

# Load .env early so Flask CLI picks it up too
load_dotenv(override=True)

def create_app():
    cfg = Config.from_env()

    app = Flask(__name__)
    # Timezone helper for routes/logging
    app.LOCAL_TZ = ZoneInfo(cfg.timezone or "Asia/Singapore")

    # Core config (pull from cfg)
    app.config.update(
        TIMEZONE=cfg.timezone,
        DATABASE_URL=cfg.database_url,
        SEASON_LABEL=cfg.season_label,
        PL_CODE=cfg.pl_code,
        SECRET_KEY=cfg.secret_key,
        # Cross-site cookie session (frontend on Vercel, API on Render)
        SESSION_COOKIE_SECURE=cfg.session_cookie_secure,  # set 1 in prod
        SESSION_COOKIE_SAMESITE="None",                   # important for cross-site cookies
    )

    # DB init + create tables (OK for now; consider migrations later)
    engine, _ = init_db(cfg.database_url)
    Base.metadata.create_all(engine)

    # Auth + routes
    login_manager.init_app(app)
    register_blueprints(app)

    # --- CORS ---
    # Prefer a single explicit frontend origin (no '*' with credentials)
    allowed_origins = []
    if getattr(cfg, "frontend_url", None):
        allowed_origins.append(cfg.frontend_url)

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins or []}},
        supports_credentials=True,  # needed for Flask-Login cookies
    )

    # --- Scheduler ---
    # In production, run the scheduler as a separate Render "Background Worker":
    #   Start command:  python -m backend.scheduler
    # For local dev, you can enable it by setting ENABLE_SCHEDULER=1
    if os.getenv("ENABLE_SCHEDULER") in ("1", "true", "True"):
        from .scheduler import start_scheduler
        start_scheduler(app)

    return app
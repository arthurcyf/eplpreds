# backend/__init__.py
from flask import Flask
from dotenv import load_dotenv
import os

from .config import Config
from .db import init_db, Base
from .models import Match  # ensure model is imported so metadata sees it
from .routes import register_blueprints
from .scheduler import start_scheduler

__all__ = ["create_app"]

# Load .env early so Flask CLI picks it up too
load_dotenv(override=True)

def create_app():
    cfg = Config.from_env()

    app = Flask(__name__)
    # expose a few settings to the app (handy for routes/logging)
    app.config.update(
        TIMEZONE=cfg.timezone,
        DATABASE_URL=cfg.database_url,
        PORT=cfg.port,
        SEASON_LABEL=cfg.season_label,
        PL_CODE=cfg.pl_code,
        SECRET_KEY=cfg.secret_key,
        SESSION_COOKIE_SECURE=cfg.session_cookie_secure,  # keep False in dev (HTTP)
        SESSION_COOKIE_SAMESITE="Lax"
    )

    # DB init + create tables
    engine, _ = init_db(cfg.database_url)
    Base.metadata.create_all(engine)

    # routes
    register_blueprints(app)

    # start scheduler only in the main process (and allow disabling via env)
    if os.environ.get("DISABLE_SCHEDULER") not in ("1", "true", "True"):
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            start_scheduler(app)

    return app
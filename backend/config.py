import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    port: int = int(os.getenv("PORT", 3000))
    timezone: str = os.getenv("TIMEZONE", "Asia/Singapore")
    fd_token: str = os.getenv("FOOTBALL_DATA_API_KEY", "")
    database_url: str | None = os.getenv("DATABASE_URL")  # may be None!
    pl_code: str = "PL"
    season_label: str = "2025/26"
    secret_key: str = os.getenv("SECRET_KEY", "dev-change-me")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "0") in ("1","true","True")

    @classmethod
    def from_env(cls) -> "Config":
        # Ensure .env is loaded even if called during import-time
        load_dotenv(override=True)

        c = cls()

        # fallback if DATABASE_URL missing
        if not c.database_url:
            c.database_url = "sqlite:///epl.db"

        # normalize postgres URLs to psycopg3 only if it's a string
        if isinstance(c.database_url, str):
            if c.database_url.startswith("postgres://"):
                c.database_url = c.database_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif c.database_url.startswith("postgresql://"):
                c.database_url = c.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

        return c
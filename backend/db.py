# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url: str):
    global engine, SessionLocal
    url = make_url(database_url)

    kwargs = dict(future=True, pool_pre_ping=True)

    # Postgres-specific tweaks
    if url.get_backend_name().startswith("postgresql"):
        # If driver is psycopg3 (scheme: postgresql+psycopg)
        if url.get_driver_name() == "psycopg":
            kwargs["connect_args"] = {
                "sslmode": "require",
                "prepare_threshold": 0,   # disable server-side PREPARE (PgBouncer-friendly)
            }
        else:
            # e.g. psycopg2: only sslmode is relevant
            kwargs["connect_args"] = {"sslmode": "require"}

    engine = create_engine(database_url, **kwargs)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    return engine, SessionLocal
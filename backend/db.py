# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url: str):
    """
    Create the SQLAlchemy engine/session.
    - For Postgres (psycopg v3), force SSL and disable server-side PREPARE
      to play nicely with PgBouncer transaction pooling.
    - For other DBs (e.g., SQLite), use defaults.
    """
    global engine, SessionLocal

    url = make_url(database_url)
    kwargs = dict(future=True, pool_pre_ping=True)

    # Apply Postgres-specific connect args
    if url.get_backend_name().startswith("postgresql"):
        kwargs["connect_args"] = {
            "sslmode": "require",     # managed PG/Supabase needs SSL
            "prepare_threshold": 0,   # <-- disable server-side prepared statements
        }

    engine = create_engine(database_url, **kwargs)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    return engine, SessionLocal
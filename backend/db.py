# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url: str):
    global engine, SessionLocal
    engine = create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require",                 # managed PG/Supabase
            "prepare_threshold": 0,               # <-- disable PREPARE entirely
            "prepared_statement_cache_size": 0,   # <-- and its cache
        },
    )
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    return engine, SessionLocal

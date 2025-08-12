from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url: str):
    global engine, SessionLocal
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    return engine, SessionLocal
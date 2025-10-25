"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": bool(getattr(settings, "DEBUG", False)),
}

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        **engine_kwargs
    )
else:
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Create tables if possible. Do not crash app on failure; log and continue.
    """
    try:
        # import models to register metadata
        from app.models.country import Country  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created or verified")
    except Exception as exc:
        logging.warning(f"Database init failed: {exc}")
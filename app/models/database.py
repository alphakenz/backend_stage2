"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

# Configure engine kwargs depending on DB type
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": bool(getattr(settings, "DEBUG", False))
}

# SQLite needs a special connect_args
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        **engine_kwargs
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables (safe: catches errors so startup doesn't crash)
    """
    try:
        from app.models.country import Country, AppStatus
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.warning(f"Could not initialize database at startup: {e}")
"""
Configuration settings for the application
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "Country Currency & Exchange API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (Railway/Heroku style)
    DATABASE_URL: str = (
        os.getenv("DATABASE_URL")
        or os.getenv("MYSQL_URL")
        or os.getenv("MYSQLURL")
        or "mysql+pymysql://root:password@localhost:3306/country_api"
    )

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # Image cache
    CACHE_DIR: str = os.getenv("CACHE_DIR", "cache")
    IMAGE_FILENAME: str = os.getenv("IMAGE_FILENAME", "summary.png")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    try:
        host_part = settings.DATABASE_URL.split("@")[1].split("/")[0] if "@" in settings.DATABASE_URL else "local"
    except Exception:
        host_part = "unknown"
    logging.debug(f"[CONFIG] Database host: {host_part}")
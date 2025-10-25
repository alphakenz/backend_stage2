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
    
    # Debug
    DEBUG: bool = False

    # Database - CRITICAL: Check multiple possible variable names
    DATABASE_URL: str = (
        os.getenv("DATABASE_URL") or
        os.getenv("MYSQL_URL") or
        os.getenv("MYSQLURL") or
        "mysql+pymysql://root:password@localhost:3306/country_api"
    )
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # External APIs
    COUNTRIES_API_URL: str = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    EXCHANGE_API_URL: str = "https://open.er-api.com/v6/latest/USD"
    
    # Cache
    CACHE_DIR: str = "cache"
    IMAGE_FILENAME: str = "summary.png"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Only log non-sensitive info when DEBUG is enabled
if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    try:
        host_part = settings.DATABASE_URL.split("@")[1].split("/")[0] if "@" in settings.DATABASE_URL else "local"
    except Exception:
        host_part = "unknown"
    logging.debug(f"[CONFIG] Database host: {host_part}")
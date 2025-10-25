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

# Debug: Print database URL (remove host/password for security)
if settings.DATABASE_URL:
    # Extract just the host part for debugging
    if "@" in settings.DATABASE_URL:
        host_part = settings.DATABASE_URL.split("@")[1].split("/")[0]
        print(f"[CONFIG] Connecting to MySQL at: {host_part}")
    else:
        print(f"[CONFIG] Database URL configured")
else:
    print("[CONFIG] WARNING: No DATABASE_URL found!")
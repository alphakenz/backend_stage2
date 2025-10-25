"""
Configuration settings for the application
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "Country Currency & Exchange API"
    APP_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
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
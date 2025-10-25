"""
Database models for countries and application status
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from datetime import datetime
from app.models.database import Base


class Country(Base):
    """Country model representing country data"""
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    population = Column(BigInteger, nullable=True)
    currency_code = Column(String(10), nullable=True, index=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(500), nullable=True)
    last_refreshed_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    def __repr__(self):
        return f"<Country(name='{self.name}', region='{self.region}')>"


class AppStatus(Base):
    """Application status model for tracking refresh metadata"""
    __tablename__ = "app_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    total_countries = Column(Integer, default=0)
    last_refreshed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AppStatus(total_countries={self.total_countries})>"
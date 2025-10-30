from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True, index=True)
    population = Column(BigInteger, nullable=False)
    currency_code = Column(String(10), nullable=True, index=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(512), nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class RefreshStatus(Base):
    __tablename__ = "refresh_status"
    
    id = Column(Integer, primary_key=True, default=1)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    total_countries = Column(Integer, default=0)
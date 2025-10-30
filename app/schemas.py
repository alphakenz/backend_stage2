from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class CountryBase(BaseModel):
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None

class CountryCreate(CountryBase):
    pass

class CountryUpdate(CountryBase):
    pass

class CountryResponse(CountryBase):
    id: int
    last_refreshed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class RefreshStatusResponse(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime]

class RefreshResponse(BaseModel):
    message: str
    total_countries: int
    last_refreshed_at: datetime

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
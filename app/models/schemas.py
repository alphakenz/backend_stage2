"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CountryResponse(BaseModel):
    """Schema for country response"""
    id: int
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: Optional[int] = None
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None
    last_refreshed_at: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object to schema"""
        data = {
            "id": obj.id,
            "name": obj.name,
            "capital": obj.capital,
            "region": obj.region,
            "population": obj.population,
            "currency_code": obj.currency_code,
            "exchange_rate": obj.exchange_rate,
            "estimated_gdp": obj.estimated_gdp,
            "flag_url": obj.flag_url,
            "last_refreshed_at": obj.last_refreshed_at.isoformat() + "Z" if obj.last_refreshed_at else None
        }
        return cls(**data)


class StatusResponse(BaseModel):
    """Schema for status response"""
    total_countries: int
    last_refreshed_at: Optional[str] = None


class RefreshResponse(BaseModel):
    """Schema for refresh response"""
    message: str
    total_countries: int
    last_refreshed_at: str


class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str
    details: Optional[dict] = None
"""
API endpoints and routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from app.core.config import settings
from app.models.database import get_db
from app.models.country import Country, AppStatus
from app.models.schemas import CountryResponse, StatusResponse, RefreshResponse
import logging
import httpx
from datetime import datetime
import random
from typing import Optional, List

router = APIRouter()

# Helper error type
class ExternalAPIError(Exception):
    pass

# Helper functions
def process_and_upsert_countries(db, countries_data, rates_data):
    """
    Process country data from external APIs and upsert into database
    """
    exchange_rates = rates_data.get("rates", {})
    
    for country_item in countries_data:
        name = country_item.get("name")
        if not name:
            continue
        
        capital = country_item.get("capital")
        region = country_item.get("region")
        population = country_item.get("population")
        flag_url = country_item.get("flag")
        
        # Get currency code
        currencies = country_item.get("currencies", [])
        currency_code = None
        if currencies and len(currencies) > 0:
            currency_code = currencies[0].get("code")
        
        # Get exchange rate
        exchange_rate = None
        if currency_code and currency_code in exchange_rates:
            exchange_rate = exchange_rates[currency_code]
        
        # Calculate estimated GDP
        estimated_gdp = None
        if population and exchange_rate:
            # Simple GDP estimation formula
            estimated_gdp = (population * random.uniform(1000, 2000)) / exchange_rate
        
        # Check if country exists
        existing_country = db.query(Country).filter(Country.name == name).first()
        
        if existing_country:
            # Update existing country
            existing_country.capital = capital
            existing_country.region = region
            existing_country.population = population
            existing_country.currency_code = currency_code
            existing_country.exchange_rate = exchange_rate
            existing_country.estimated_gdp = estimated_gdp
            existing_country.flag_url = flag_url
            existing_country.last_refreshed_at = datetime.utcnow()
        else:
            # Create new country
            new_country = Country(
                name=name,
                capital=capital,
                region=region,
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=estimated_gdp,
                flag_url=flag_url,
                last_refreshed_at=datetime.utcnow()
            )
            db.add(new_country)
    
    # Update or create app status
    total_countries = db.query(Country).count()
    app_status = db.query(AppStatus).first()
    
    if app_status:
        app_status.total_countries = total_countries
        app_status.last_refreshed_at = datetime.utcnow()
    else:
        app_status = AppStatus(
            total_countries=total_countries,
            last_refreshed_at=datetime.utcnow()
        )
        db.add(app_status)
    
    db.commit()


def compute_summary(db):
    """
    Compute summary statistics and get top 5 countries by GDP
    """
    total_countries = db.query(Country).count()
    top_5_countries = db.query(Country).filter(
        Country.estimated_gdp.isnot(None)
    ).order_by(desc(Country.estimated_gdp)).limit(5).all()
    
    app_status = db.query(AppStatus).first()
    timestamp = app_status.last_refreshed_at if app_status else datetime.utcnow()
    
    return total_countries, top_5_countries, timestamp


# Move async httpx usage into a proper async helper (no async at import-time)
async def fetch_external_data():
    countries_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    rates_url = "https://open.er-api.com/v6/latest/USD"
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp_c = await client.get(countries_url)
        if resp_c.status_code != 200:
            raise ExternalAPIError(f"Could not fetch countries: {resp_c.status_code}")
        countries_data = resp_c.json()

        resp_r = await client.get(rates_url)
        if resp_r.status_code != 200:
            raise ExternalAPIError(f"Could not fetch rates: {resp_r.status_code}")
        rates_data = resp_r.json()

    return countries_data, rates_data


@router.post("/countries/refresh", tags=["Countries"])
async def refresh_countries(db=Depends(get_db)):
    """
    Fetch external APIs then perform DB upserts and image generation.
    If any external fetch fails, return 503 and do not modify DB.
    """
    # Fetch external data first
    try:
        countries_data, rates = await fetch_external_data()
    except ExternalAPIError as e:
        logging.warning(f"External fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "External data source unavailable", "details": str(e)}
        )

    # Apply DB changes in a transaction (commit only on success)
    try:
        with db.begin():
            process_and_upsert_countries(db, countries_data, rates)
    except SQLAlchemyError:
        logging.exception("DB operation failed during refresh")
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})

    # Generate image after DB commit
    try:
        total, top5, ts = compute_summary(db)
        from app.core.image_generator import generate_summary_image
        generate_summary_image("Summary", top5, ts)
    except Exception:
        logging.warning("Failed to generate summary image; continuing")

        # Get updated status
    app_status = db.query(AppStatus).first()
    total = app_status.total_countries if app_status else 0
    last_refreshed = app_status.last_refreshed_at.isoformat() + "Z" if app_status and app_status.last_refreshed_at else None
    
    return {
        "message": "Countries refreshed successfully",
        "total_countries": total,
        "last_refreshed_at": last_refreshed or datetime.utcnow().isoformat() + "Z"
    }


@router.get("/countries", response_model=List[CountryResponse], tags=["Countries"])
async def get_countries(
    region: Optional[str] = Query(None, description="Filter by region"),
    currency: Optional[str] = Query(None, description="Filter by currency code"),
    sort: Optional[str] = Query(None, description="Sort order: gdp_desc, gdp_asc, pop_desc, pop_asc"),
    db=Depends(get_db)
):
    """
    Get all countries with optional filtering and sorting
    """
    query = db.query(Country)
    
    # Apply filters
    if region:
        query = query.filter(Country.region == region)
    
    if currency:
        query = query.filter(Country.currency_code == currency)
    
    # Apply sorting
    if sort:
        if sort == "gdp_desc":
            query = query.order_by(desc(Country.estimated_gdp))
        elif sort == "gdp_asc":
            query = query.order_by(Country.estimated_gdp)
        elif sort == "pop_desc":
            query = query.order_by(desc(Country.population))
        elif sort == "pop_asc":
            query = query.order_by(Country.population)
    
    countries = query.all()
    return [CountryResponse.from_orm(country) for country in countries]


@router.get("/countries/{name}", response_model=CountryResponse, tags=["Countries"])
async def get_country(name: str, db=Depends(get_db)):
    """
    Get a single country by name
    """
    country = db.query(Country).filter(Country.name == name).first()
    
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
    
    return CountryResponse.from_orm(country)


@router.delete("/countries/{name}", tags=["Countries"])
async def delete_country(name: str, db=Depends(get_db)):
    """
    Delete a country by name
    """
    country = db.query(Country).filter(Country.name == name).first()
    
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
    
    db.delete(country)
    db.commit()
    
    # Update app status
    app_status = db.query(AppStatus).first()
    if app_status:
        app_status.total_countries = db.query(Country).count()
        db.commit()
    
    return {"message": f"Country '{name}' deleted successfully"}


@router.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status(db=Depends(get_db)):
    """
    Get application status including total countries and last refresh time
    """
    app_status = db.query(AppStatus).first()
    
    if not app_status:
        return StatusResponse(
            total_countries=0,
            last_refreshed_at=None
        )
    
    last_refreshed = app_status.last_refreshed_at.isoformat() + "Z" if app_status.last_refreshed_at else None
    
    return StatusResponse(
        total_countries=app_status.total_countries,
        last_refreshed_at=last_refreshed
    )


@router.get("/countries/image", tags=["Image"])
async def get_summary_image():
    """
    Get the generated summary image
    """
    image_path = Path(settings.CACHE_DIR) / settings.IMAGE_FILENAME
    if not image_path.exists():
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    return FileResponse(image_path, media_type="image/png")
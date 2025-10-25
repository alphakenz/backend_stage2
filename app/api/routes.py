"""
API endpoints and routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
import httpx
import random
from datetime import datetime

from app.core.config import settings
from app.models.database import get_db, SessionLocal
from app.models.country import Country, AppStatus
from app.models.schemas import CountryResponse, StatusResponse, RefreshResponse
from app.core.image_generator import generate_summary_image

router = APIRouter()


@router.post("/countries/refresh", tags=["Countries"])
def refresh_countries(db=Depends(get_db)):
    """
    Fetch external APIs then perform DB upserts and image generation.
    If any external fetch fails, return 503 and do not modify DB.
    """
    # 1) Fetch external data first (existing code)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            countries_response = await client.get(settings.COUNTRIES_API_URL)
            if countries_response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "External data source unavailable",
                        "details": "Could not fetch data from restcountries API"
                    }
                )
            countries_data = countries_response.json()

            # Fetch exchange rates
            exchange_response = await client.get(settings.EXCHANGE_API_URL)
            if exchange_response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "External data source unavailable",
                        "details": "Could not fetch data from exchange rates API"
                    }
                )
            exchange_data = exchange_response.json()
            exchange_rates = exchange_data.get("rates", {})

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": "Request timeout while fetching external data"
            }
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": f"Network error: {str(e)}"
            }
        )

    # 2) Apply DB changes in a transaction — commit only if processing succeeded
    try:
        refresh_timestamp = datetime.utcnow()
        processed_count = 0

        for country_data in countries_data:
            name = country_data.get("name")
            if not name:
                continue

            capital = country_data.get("capital")
            region = country_data.get("region")
            population = country_data.get("population")
            flag_url = country_data.get("flag")
            currencies = country_data.get("currencies", [])

            # Handle currency
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0

            if currencies and len(currencies) > 0:
                currency_code = currencies[0].get("code")
                
                if currency_code and currency_code in exchange_rates:
                    exchange_rate = exchange_rates[currency_code]
                    if population and exchange_rate:
                        random_multiplier = random.uniform(1000, 2000)
                        estimated_gdp = (population * random_multiplier) / exchange_rate
                elif currency_code:
                    # Currency code exists but not in exchange rates
                    exchange_rate = None
                    estimated_gdp = None

            # Check if country exists (case-insensitive)
            existing_country = db.query(Country).filter(
                Country.name.ilike(name)
            ).first()

            if existing_country:
                # Update existing country
                existing_country.capital = capital
                existing_country.region = region
                existing_country.population = population
                existing_country.currency_code = currency_code
                existing_country.exchange_rate = exchange_rate
                existing_country.estimated_gdp = estimated_gdp
                existing_country.flag_url = flag_url
                existing_country.last_refreshed_at = refresh_timestamp
            else:
                # Insert new country
                new_country = Country(
                    name=name,
                    capital=capital,
                    region=region,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp,
                    flag_url=flag_url,
                    last_refreshed_at=refresh_timestamp
                )
                db.add(new_country)
            
            processed_count += 1

        # Update or create app status
        app_status = db.query(AppStatus).first()
        if app_status:
            app_status.last_refreshed_at = refresh_timestamp
            app_status.total_countries = processed_count
        else:
            app_status = AppStatus(
                last_refreshed_at=refresh_timestamp,
                total_countries=processed_count
            )
            db.add(app_status)

        db.commit()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})

    # 3) Generate image after DB commit (use settings)
    try:
        total, top5, ts = compute_summary(db)  # existing helper to compute totals/top5
        generate_summary_image("Summary", top5, ts)
    except Exception:
        logging.warning("Failed to generate summary image; continuing")

    return {"status": "ok"}


@router.get("/countries", response_model=List[CountryResponse], tags=["Countries"])
async def get_countries(
    region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all countries from database with optional filters and sorting.
    
    Query Parameters:
    - region: Filter by geographic region
    - currency: Filter by currency code
    - sort: Sort results (gdp_desc, gdp_asc, population_desc, population_asc)
    """
    query = db.query(Country)

    # Apply filters
    if region:
        query = query.filter(Country.region.ilike(region))
    
    if currency:
        query = query.filter(Country.currency_code.ilike(currency))

    # Apply sorting
    if sort:
        if sort == "gdp_desc":
            query = query.order_by(Country.estimated_gdp.desc().nullslast())
        elif sort == "gdp_asc":
            query = query.order_by(Country.estimated_gdp.asc().nullsfirst())
        elif sort == "population_desc":
            query = query.order_by(Country.population.desc().nullslast())
        elif sort == "population_asc":
            query = query.order_by(Country.population.asc().nullsfirst())

    countries = query.all()
    return countries


@router.get("/countries/{name}", response_model=CountryResponse, tags=["Countries"])
async def get_country(name: str, db: Session = Depends(get_db)):
    """
    Get a single country by name (case-insensitive).
    
    Path Parameters:
    - name: Country name
    """
    country = db.query(Country).filter(Country.name.ilike(name)).first()
    
    if not country:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    
    return country


@router.delete("/countries/{name}", tags=["Countries"])
async def delete_country(name: str, db: Session = Depends(get_db)):
    """
    Delete a country record from the database.
    
    Path Parameters:
    - name: Country name to delete
    """
    country = db.query(Country).filter(Country.name.ilike(name)).first()
    
    if not country:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    
    db.delete(country)
    db.commit()
    
    return {"message": f"Country '{name}' deleted successfully"}


@router.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status(db: Session = Depends(get_db)):
    """
    Get API status including total countries and last refresh timestamp.
    """
    app_status = db.query(AppStatus).first()
    
    if not app_status:
        return {
            "total_countries": 0,
            "last_refreshed_at": None
        }
    
    return {
        "total_countries": app_status.total_countries,
        "last_refreshed_at": app_status.last_refreshed_at.isoformat() + "Z" if app_status.last_refreshed_at else None
    }


# Image endpoint
@router.get("/countries/image", tags=["Image"])
async def get_summary_image():
    image_path = Path(settings.CACHE_DIR) / settings.IMAGE_FILENAME
    if not image_path.exists():
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    return FileResponse(image_path, media_type="image/png")
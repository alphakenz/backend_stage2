from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import logging
import asyncio

from app.database import get_db, engine, Base
from app import models, schemas, crud
from app.external_apis import external_api_service
from app.image_generator import image_generator
from app.utils import RefreshLock

app = FastAPI(title="Country API", version="1.0.0")
logger = logging.getLogger(__name__)

refresh_lock = RefreshLock()

@app.on_event("startup")
async def startup_event():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/countries/refresh", response_model=schemas.RefreshResponse)
async def refresh_countries(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Refresh country data from external APIs"""
    if refresh_lock.is_locked():
        raise HTTPException(status_code=429, detail="Refresh already in progress")
    
    try:
        refresh_lock.lock()
        
        # Fetch data from external APIs
        countries_data = await external_api_service.fetch_countries()
        exchange_rates = await external_api_service.fetch_exchange_rates()
        
        # Process and update countries
        total_processed = 0
        for country_data in countries_data:
            currency_code = external_api_service.extract_currency_code(country_data.get("currencies", []))
            exchange_rate = exchange_rates.get(currency_code) if currency_code else None
            
            estimated_gdp = external_api_service.compute_estimated_gdp(
                country_data["population"], 
                exchange_rate
            )
            
            # Prepare country data
            country_dict = {
                "name": country_data["name"],
                "capital": country_data.get("capital"),
                "region": country_data["region"],
                "population": country_data["population"],
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "estimated_gdp": estimated_gdp,
                "flag_url": country_data.get("flag"),
                "last_refreshed_at": datetime.datetime.utcnow()
            }
            
            # Update or create country
            existing_country = await crud.country_crud.get_country_by_name(db, country_data["name"])
            if existing_country:
                await crud.country_crud.update_country(db, existing_country, country_dict)
            else:
                await crud.country_crud.create_country(db, country_dict)
            
            total_processed += 1
        
        # Update refresh status
        await crud.country_crud.update_refresh_status(db, total_processed)
        
        # Generate summary image in background
        background_tasks.add_task(generate_summary_image, db)
        
        status = await crud.country_crud.get_refresh_status(db)
        return {
            "message": "Refresh successful",
            "total_countries": total_processed,
            "last_refreshed_at": status.last_refreshed_at
        }
        
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        if "Countries API" in str(e):
            raise HTTPException(
                status_code=503, 
                detail={"error": "External data source unavailable", "details": "Could not fetch data from Countries API"}
            )
        elif "Exchange Rates API" in str(e):
            raise HTTPException(
                status_code=503, 
                detail={"error": "External data source unavailable", "details": "Could not fetch data from Exchange Rates API"}
            )
        else:
            raise HTTPException(status_code=500, detail={"error": "Internal server error"})
    finally:
        refresh_lock.unlock()

async def generate_summary_image(db: AsyncSession):
    """Generate summary image after refresh"""
    try:
        countries = await crud.country_crud.get_countries(db, sort_gdp=True)
        status = await crud.country_crud.get_refresh_status(db)
        
        top_countries = [
            {
                "name": country.name,
                "estimated_gdp": country.estimated_gdp
            }
            for country in countries if country.estimated_gdp is not None
        ]
        
        image_generator.generate_image(
            status.total_countries,
            top_countries,
            status.last_refreshed_at
        )
    except Exception as e:
        logger.error(f"Failed to generate summary image: {e}")

@app.get("/countries", response_model=List[schemas.CountryResponse])
async def get_countries(
    region: Optional[str] = Query(None, description="Filter by region"),
    currency: Optional[str] = Query(None, description="Filter by currency code"),
    sort: Optional[str] = Query(None, description="Sort by GDP (use 'gdp_desc')"),
    db: AsyncSession = Depends(get_db)
):
    """Get all countries with optional filtering and sorting"""
    sort_gdp = sort == "gdp_desc"
    countries = await crud.country_crud.get_countries(db, region, currency, sort_gdp)
    return countries

@app.get("/countries/{name}", response_model=schemas.CountryResponse)
async def get_country(name: str, db: AsyncSession = Depends(get_db)):
    """Get a specific country by name"""
    country = await crud.country_crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return country

@app.delete("/countries/{name}")
async def delete_country(name: str, db: AsyncSession = Depends(get_db)):
    """Delete a country by name"""
    country = await crud.country_crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    
    await crud.country_crud.delete_country(db, country)
    return {"message": "Deleted"}

@app.get("/status", response_model=schemas.RefreshStatusResponse)
async def get_status(db: AsyncSession = Depends(get_db)):
    """Get refresh status"""
    status = await crud.country_crud.get_refresh_status(db)
    return status

@app.get("/countries/image")
async def get_summary_image():
    """Get the generated summary image"""
    image_path = "cache/summary.png"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    
    return FileResponse(image_path, media_type="image/png")

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
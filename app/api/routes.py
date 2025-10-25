"""
API endpoints and routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.models.database import get_db
import logging
import httpx

router = APIRouter()

# helper error
class ExternalAPIError(Exception):
    pass

# Move httpx usage into an async helper (no async at import time)
async def fetch_external_data():
    countries_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    rates_url = "https://open.er-api.com/v6/latest/USD"
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp_c = await client.get(countries_url)
        if resp_c.status_code != 200:
            raise ExternalAPIError("Could not fetch countries")
        countries_data = resp_c.json()

        resp_r = await client.get(rates_url)
        if resp_r.status_code != 200:
            raise ExternalAPIError("Could not fetch rates")
        rates_data = resp_r.json()

    return countries_data, rates_data


@router.post("/countries/refresh", tags=["Countries"])
async def refresh_countries(db=Depends(get_db)):
    """
    Fetch external APIs then perform DB upserts and image generation.
    If any external fetch fails, return 503 and do not modify DB.
    """
    # 1) Fetch external data first (async helper)
    try:
        countries_data, rates = await fetch_external_data()
    except ExternalAPIError as e:
        logging.warning(f"External fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "External data source unavailable", "details": str(e)}
        )

    # 2) Apply DB changes in a transaction — commit only if processing succeeded
    try:
        with db.begin():
            process_and_upsert_countries(db, countries_data, rates)
    except SQLAlchemyError:
        logging.exception("DB operation failed during refresh")
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})

    # 3) Generate image after DB commit (use settings)
    try:
        total, top5, ts = compute_summary(db)
        from app.core.image_generator import generate_summary_image
        generate_summary_image("Summary", top5, ts)
    except Exception:
        logging.warning("Failed to generate summary image; continuing")

    return {"status": "ok"}


@router.get("/countries/image", tags=["Image"])
async def get_summary_image():
    image_path = Path(settings.CACHE_DIR) / settings.IMAGE_FILENAME
    if not image_path.exists():
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    return FileResponse(image_path, media_type="image/png")
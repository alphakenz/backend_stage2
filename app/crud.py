from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, and_
from typing import List, Optional
from app import models, schemas
import datetime

class CountryCRUD:
    async def get_country_by_name(self, db: AsyncSession, name: str) -> Optional[models.Country]:
        result = await db.execute(
            select(models.Country).where(models.Country.name.ilike(name))
        )
        return result.scalar_one_or_none()
    
    async def get_countries(
        self, 
        db: AsyncSession, 
        region: Optional[str] = None,
        currency: Optional[str] = None,
        sort_gdp: bool = False
    ) -> List[models.Country]:
        query = select(models.Country)
        
        if region:
            query = query.where(models.Country.region == region)
        if currency:
            query = query.where(models.Country.currency_code == currency)
        if sort_gdp:
            query = query.order_by(desc(models.Country.estimated_gdp))
        else:
            query = query.order_by(models.Country.name)
            
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_country(self, db: AsyncSession, country_data: dict) -> models.Country:
        db_country = models.Country(**country_data)
        db.add(db_country)
        await db.commit()
        await db.refresh(db_country)
        return db_country
    
    async def update_country(self, db: AsyncSession, db_country: models.Country, update_data: dict) -> models.Country:
        for field, value in update_data.items():
            setattr(db_country, field, value)
        db_country.last_refreshed_at = datetime.datetime.utcnow()
        await db.commit()
        await db.refresh(db_country)
        return db_country
    
    async def delete_country(self, db: AsyncSession, country: models.Country):
        await db.delete(country)
        await db.commit()
    
    async def get_refresh_status(self, db: AsyncSession) -> models.RefreshStatus:
        result = await db.execute(select(models.RefreshStatus))
        status = result.scalar_one_or_none()
        if not status:
            status = models.RefreshStatus()
            db.add(status)
            await db.commit()
            await db.refresh(status)
        return status
    
    async def update_refresh_status(self, db: AsyncSession, total_countries: int):
        status = await self.get_refresh_status(db)
        status.total_countries = total_countries
        status.last_refreshed_at = datetime.datetime.utcnow()
        await db.commit()

country_crud = CountryCRUD()
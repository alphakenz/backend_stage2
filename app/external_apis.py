import httpx
import random
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExternalAPIService:
    def __init__(self):
        self.timeout = 30.0  # Increased timeout for external APIs
        
    async def fetch_countries(self) -> List[Dict[str, Any]]:
        """Fetch country data from REST Countries API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("Countries API timeout")
            raise Exception("Could not fetch data from Countries API")
        except Exception as e:
            logger.error(f"Failed to fetch countries: {e}")
            raise Exception("Could not fetch data from Countries API")
    
    async def fetch_exchange_rates(self) -> Dict[str, float]:
        """Fetch exchange rates from Open Exchange Rates API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://open.er-api.com/v6/latest/USD")
                response.raise_for_status()
                data = response.json()
                if data.get("result") == "success":
                    return data.get("rates", {})
                else:
                    raise Exception("Exchange rates API returned error")
        except httpx.TimeoutException:
            logger.error("Exchange rates API timeout")
            raise Exception("Could not fetch data from Exchange Rates API")
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            raise Exception("Could not fetch data from Exchange Rates API")
    
    def compute_estimated_gdp(self, population: int, exchange_rate: Optional[float]) -> Optional[float]:
        """Compute estimated GDP using population, exchange rate, and random multiplier"""
        if exchange_rate is None or exchange_rate == 0:
            return None
            
        random_multiplier = random.randint(1000, 2000)
        return (population * random_multiplier) / exchange_rate
    
    def extract_currency_code(self, currencies: List[Dict]) -> Optional[str]:
        """Extract currency code from currencies array"""
        if not currencies:
            return None
        return currencies[0].get("code")

external_api_service = ExternalAPIService()
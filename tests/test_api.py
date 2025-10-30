import pytest
from unittest.mock import patch, AsyncMock
import json

def test_get_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert "total_countries" in response.json()
    assert "last_refreshed_at" in response.json()

def test_get_country_not_found(client):
    response = client.get("/countries/NonexistentCountry")
    assert response.status_code == 404
    assert response.json()["error"] == "Country not found"

def test_delete_country_not_found(client):
    response = client.delete("/countries/NonexistentCountry")
    assert response.status_code == 404
    assert response.json()["error"] == "Country not found"

@patch('app.external_apis.external_api_service.fetch_countries')
@patch('app.external_apis.external_api_service.fetch_exchange_rates')
def test_refresh_success(mock_rates, mock_countries, client):
    # Mock external API responses
    mock_countries.return_value = AsyncMock(return_value=[
        {
            "name": "Test Country",
            "capital": "Test Capital", 
            "region": "Test Region",
            "population": 1000000,
            "flag": "https://flagcdn.com/tc.svg",
            "currencies": [{"code": "TST", "name": "Test Currency", "symbol": "T"}]
        }
    ])
    
    mock_rates.return_value = AsyncMock(return_value={"TST": 1.5})
    
    response = client.post("/countries/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Refresh successful"
    assert "total_countries" in data

@patch('app.external_apis.external_api_service.fetch_countries')
def test_refresh_countries_api_failure(mock_countries, client):
    mock_countries.side_effect = Exception("API failure")
    
    response = client.post("/countries/refresh")
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "External data source unavailable"

def test_get_summary_image_not_found(client):
    response = client.get("/countries/image")
    assert response.status_code == 404
    assert response.json()["error"] == "Summary image not found"

def test_get_countries_with_filters(client):
    response = client.get("/countries?region=Africa")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
"""
API tests for Country Currency & Exchange API
Run with: pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, get_db
from app.main import app

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up database before each test"""
    yield
    # Cleanup after test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "version" in data


class TestStatusEndpoint:
    """Tests for status endpoint"""
    
    def test_status_endpoint_empty(self):
        """Test status endpoint when no data exists"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["total_countries"] == 0
        assert data["last_refreshed_at"] is None


class TestCountriesEndpoint:
    """Tests for countries endpoints"""
    
    def test_get_countries_empty(self):
        """Test getting countries when database is empty"""
        response = client.get("/countries")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_country_not_found(self):
        """Test getting non-existent country"""
        response = client.get("/countries/NonExistentCountry")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "Country not found"
    
    def test_delete_country_not_found(self):
        """Test deleting non-existent country"""
        response = client.delete("/countries/NonExistentCountry")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_filter_by_region(self):
        """Test filtering countries by region"""
        response = client.get("/countries?region=Africa")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_filter_by_currency(self):
        """Test filtering countries by currency"""
        response = client.get("/countries?currency=USD")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_sort_by_gdp(self):
        """Test sorting countries by GDP"""
        response = client.get("/countries?sort=gdp_desc")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestImageEndpoint:
    """Tests for image endpoint"""
    
    def test_get_image_not_found(self):
        """Test getting image when it doesn't exist"""
        response = client.get("/countries/image")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "Summary image not found"


class TestRefreshEndpoint:
    """Tests for refresh endpoint"""
    
    def test_refresh_countries(self):
        """Test refreshing countries from external APIs"""
        response = client.post("/countries/refresh")
        
        # This will fail if external APIs are down, but that's expected
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "total_countries" in data
            assert "last_refreshed_at" in data
            assert data["total_countries"] > 0
        elif response.status_code == 503:
            # External API unavailable - this is acceptable in tests
            data = response.json()
            assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
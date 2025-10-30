# Countries API

A RESTful API built with FastAPI that fetches country data and exchange rates from external APIs, calculates estimated GDP, and provides CRUD operations with data caching in MySQL.

## Features

- 🌍 Fetch and cache country data from restcountries.com
- 💱 Integrate real-time exchange rates from open.er-api.com
- 📊 Calculate estimated GDP per country
- 🖼️ Generate summary image with top 5 countries by GDP
- 🔍 Filter and sort countries by region, currency, and GDP
- 🔒 Thread-safe refresh operations with transaction support
- ✅ Comprehensive test suite with mocked external APIs

## Prerequisites

- Python 3.9+
- MySQL 5.7+ or 8.0+
- pip (Python package manager)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd countries-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL database

```bash
# Login to MySQL
mysql -u root -p

# Run the initialization script
source init_db.sql

# Or manually create the database
CREATE DATABASE countries_db;
```

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

Example `.env`:
```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/countries_db
PORT=8000
COUNTRIES_API=https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies
EXCHANGE_API=https://open.er-api.com/v6/latest/USD
API_TIMEOUT=10
```

## Running the Application

### Development server

```bash
uvicorn main:app --reload --port 8000
```

### Production server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=main --cov-report=html

# Run specific test file
pytest test_main.py -v
```

## API Endpoints

### POST /countries/refresh

Fetch country data and exchange rates from external APIs, calculate estimated GDP, and update the database.

**Request:**
```bash
curl -X POST http://localhost:8000/countries/refresh
```

**Success Response (200):**
```json
{
  "message": "Refresh successful",
  "total_countries": 250,
  "last_refreshed_at": "2025-10-30T18:00:00Z"
}
```

**Error Response (503):**
```json
{
  "error": "External data source unavailable",
  "details": "Could not fetch data from restcountries.com"
}
```

### GET /countries

Retrieve all countries with optional filtering and sorting.

**Query Parameters:**
- `region` (optional): Filter by region (e.g., "Africa", "Americas")
- `currency` (optional): Filter by currency code (e.g., "NGN", "USD")
- `sort` (optional): Set to "gdp_desc" to sort by estimated GDP (descending)

**Examples:**

Get all countries:
```bash
curl http://localhost:8000/countries
```

Get all African countries:
```bash
curl "http://localhost:8000/countries?region=Africa"
```

Get all countries using NGN currency:
```bash
curl "http://localhost:8000/countries?currency=NGN"
```

Get all African countries sorted by GDP:
```bash
curl "http://localhost:8000/countries?region=Africa&sort=gdp_desc"
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-30T18:00:00Z"
  }
]
```

### GET /countries/{name}

Retrieve a single country by name (case-insensitive).

**Request:**
```bash
curl http://localhost:8000/countries/Nigeria
```

**Success Response (200):**
```json
{
  "id": 1,
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 206139589,
  "currency_code": "NGN",
  "exchange_rate": 1600.23,
  "estimated_gdp": 25767448125.2,
  "flag_url": "https://flagcdn.com/ng.svg",
  "last_refreshed_at": "2025-10-30T18:00:00Z"
}
```

**Error Response (404):**
```json
{
  "error": "Country not found"
}
```

### DELETE /countries/{name}

Delete a country by name (case-insensitive).

**Request:**
```bash
curl -X DELETE http://localhost:8000/countries/Nigeria
```

**Success Response (200):**
```json
{
  "message": "Deleted"
}
```

**Error Response (404):**
```json
{
  "error": "Country not found"
}
```

### GET /status

Get the current refresh status and total country count.

**Request:**
```bash
curl http://localhost:8000/status
```

**Response (200):**
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-30T18:00:00Z"
}
```

### GET /countries/image

Retrieve the generated summary image showing top 5 countries by estimated GDP.

**Request:**
```bash
curl http://localhost:8000/countries/image --output summary.png
```

Or open in browser:
```
http://localhost:8000/countries/image
```

**Success Response (200):**
Returns PNG image file

**Error Response (404):**
```json
{
  "error": "Summary image not found"
}
```

## Database Schema

### countries table

| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Auto-increment primary key |
| name | VARCHAR(255) | Country name (unique) |
| capital | VARCHAR(255) | Capital city |
| region | VARCHAR(255) | Geographic region |
| population | BIGINT | Population count |
| currency_code | VARCHAR(10) | Currency code (e.g., NGN) |
| exchange_rate | DOUBLE | Exchange rate vs USD |
| estimated_gdp | DOUBLE | Calculated GDP estimate |
| flag_url | VARCHAR(512) | URL to flag image |
| last_refreshed_at | TIMESTAMP | Last update timestamp |

### refresh_status table

| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Always 1 (singleton) |
| last_refreshed_at | TIMESTAMP | Last successful refresh |
| total_countries | INT | Total countries in DB |

## Business Logic

### GDP Calculation

For each country:
1. Get the first currency code from the currencies array
2. Look up exchange rate from USD
3. Generate random multiplier between 1000-2000
4. Calculate: `estimated_gdp = (population × multiplier) / exchange_rate`

**Edge Cases:**
- If currencies array is empty: `currency_code = null`, `estimated_gdp = 0`
- If exchange rate not found: `exchange_rate = null`, `estimated_gdp = null`
- Country is still stored in all cases

### Refresh Behavior

- Countries are matched by name (case-insensitive)
- Existing countries are updated, new ones are inserted
- All operations are transactional (rollback on failure)
- Concurrent refreshes are prevented with asyncio lock
- Summary image is regenerated after successful refresh

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service unavailable (external API failure) |

## Project Structure

```
backend_stage2/
├── main.py                 # FastAPI application
├── test_main.py           # Test suite
├── requirements.txt       # Python dependencies
├── init_db.sql           # Database initialization script
├── .env.example          # Environment variables template
├── README.md             # This file
└── cache/                # Generated images directory
    └── summary.png       # Summary image (generated)
```

## Docker Deployment (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: countries_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init_db.sql:/docker-entrypoint-initdb.d/init.sql

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql+pymysql://root:rootpassword@mysql:3306/countries_db
    depends_on:
      - mysql
    volumes:
      - ./cache:/app/cache

volumes:
  mysql_data:
```

**Run with Docker:**
```bash
docker-compose up -d
```

## Troubleshooting

### Database Connection Issues

If you get connection errors:
1. Verify MySQL is running: `sudo systemctl status mysql`
2. Check credentials in `.env`
3. Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### External API Timeouts

If refresh fails with 503:
1. Check internet connectivity
2. Verify API endpoints are accessible
3. Increase `API_TIMEOUT` in `.env`

### Image Generation Errors

If image generation fails:
1. Ensure `cache/` directory exists and is writable
2. Install required fonts: `sudo apt-get install fonts-dejavu`

## Performance Considerations

- Database indexes on `region`, `currency_code`, and `estimated_gdp`
- Async HTTP calls for external APIs
- Transaction rollback on failures
- Connection pooling with SQLAlchemy
- Refresh operation lock prevents concurrent updates

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.
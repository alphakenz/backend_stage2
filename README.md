# Country Currency & Exchange API

A RESTful API built with FastAPI that fetches country data from external APIs, stores it in MySQL, and provides CRUD operations with exchange rate information.

## Features

- ✅ Fetch and cache country data from REST Countries API
- ✅ Integrate real-time exchange rates
- ✅ Calculate estimated GDP for each country
- ✅ Filter by region and currency
- ✅ Sort by GDP and population
- ✅ Generate summary images with top countries
- ✅ Complete CRUD operations
- ✅ Error handling and validation

## Project Structure

```
backend_stage2/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   └── image_generator.py  # Image generation utility
│   └── models/
│       ├── __init__.py
│       ├── database.py         # Database configuration
│       ├── country.py          # Country and AppStatus models
│       └── schemas.py          # Pydantic schemas
├── tests/
│   ├── __init__.py
│   └── test_api.py             # API tests
├── cache/                      # Generated images directory
├── .env                        # Environment variables
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── Procfile                    # For deployment
└── README.md                   # This file
```

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MySQL 5.7+ / 8.0+
- **ORM**: SQLAlchemy 2.0.23
- **HTTP Client**: httpx 0.25.2
- **Image Processing**: Pillow 10.1.0
- **Validation**: Pydantic 2.5.0
- **Testing**: pytest 7.4.3

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| POST | `/countries/refresh` | Fetch and cache all country data |
| GET | `/countries` | Get all countries (with filters) |
| GET | `/countries/{name}` | Get one country by name |
| DELETE | `/countries/{name}` | Delete a country record |
| GET | `/status` | Get total countries and last refresh time |
| GET | `/countries/image` | Get summary image |

## Installation & Setup

### Prerequisites

- Python 3.9+
- MySQL 5.7+ or 8.0+
- pip

### Local Development Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd backend_stage2
```

**2. Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Mac OS 
venv\Scripts\activate # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up MySQL database**
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE country_api CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user (optional)
CREATE USER 'country_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON country_api.* TO 'country_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**5. Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

Example `.env`:
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/country_api
HOST=0.0.0.0
PORT=8000
```

**6. Run the application**
```bash
# From the backend_stage2 directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**7. Access API documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### 1. Refresh Country Data
```bash
curl -X POST http://localhost:8000/countries/refresh
```

### 2. Get All Countries
```bash
curl http://localhost:8000/countries
```

### 3. Filter by Region
```bash
curl "http://localhost:8000/countries?region=Africa"
```

### 4. Filter by Currency
```bash
curl "http://localhost:8000/countries?currency=NGN"
```

### 5. Sort by GDP (Descending)
```bash
curl "http://localhost:8000/countries?sort=gdp_desc"
```

### 6. Get Single Country
```bash
curl http://localhost:8000/countries/Nigeria
```

### 7. Get Status
```bash
curl http://localhost:8000/status
```

### 8. Get Summary Image
```bash
curl http://localhost:8000/countries/image --output summary.png
```

### 9. Delete Country
```bash
curl -X DELETE http://localhost:8000/countries/Nigeria
```

## Running Tests

```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_api.py -v

# Run with coverage
pip install pytest-cov
pytest tests/test_api.py --cov=app --cov-report=html
```

## Deployment

### Railway 

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git push
```

2. **Deploy on Railway**
   - Go to [Railway.app](https://railway.app)
   - New Project → Deploy from GitHub
   - Add MySQL database
   - Set environment variables:
     ```
     DATABASE_URL = ${{MySQL.DATABASE_URL}}
     PORT = ${{PORT}}
     ```

3. **Generate Domain**
   - Go to Settings → Generate Domain
   - Your API: `https://your-app.railway.app`


## Error Handling

The API returns consistent JSON error responses:

**404 Not Found**
```json
{
  "error": "Country not found"
}
```

**503 Service Unavailable**
```json
{
  "error": "External data source unavailable",
  "details": "Could not fetch data from restcountries API"
}
```

## Data Model

### Country Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Auto-generated primary key |
| `name` | String | Country name (required) |
| `capital` | String | Capital city (optional) |
| `region` | String | Geographic region (optional) |
| `population` | BigInteger | Population count (optional) |
| `currency_code` | String | Currency code (optional) |
| `exchange_rate` | Float | Exchange rate to USD (optional) |
| `estimated_gdp` | Float | Calculated GDP estimate (optional) |
| `flag_url` | String | Flag image URL (optional) |
| `last_refreshed_at` | DateTime | Last refresh timestamp |

### GDP Calculation

```python
estimated_gdp = (population × random(1000-2000)) ÷ exchange_rate
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **sqlalchemy**: ORM
- **pymysql**: MySQL driver
- **httpx**: Async HTTP client
- **Pillow**: Image processing
- **pydantic**: Data validation
- **pytest**: Testing framework

## Troubleshooting

**Database Connection Error**
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `.env` file
- Ensure database exists

**Module Not Found Error**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Port Already in Use**
- Change port: `uvicorn app.main:app --port 8001`
- Kill process: `lsof -ti:8000 | xargs kill -9`

**External API Timeout**
- Check internet connection
- Verify API endpoints are accessible
- Increase timeout in `app/api/routes.py` if needed

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

MIT License

## Author

Kenneth Apeh

## Acknowledgments

- REST Countries API: https://restcountries.com
- Exchange Rates API: https://www.exchangerate-api.com
- FastAPI: https://fastapi.tiangolo.com
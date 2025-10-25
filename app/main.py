"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.core.config import settings
from app.models.database import init_db

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="RESTful API for country data with exchange rates",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (optional, uncomment if needed)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Initialize database
init_db()

# Include API routes
app.include_router(routes.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "refresh": "POST /countries/refresh",
            "get_all": "GET /countries",
            "get_one": "GET /countries/{name}",
            "delete": "DELETE /countries/{name}",
            "status": "GET /status",
            "image": "GET /countries/image"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    import os
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Debug: Print all MySQL-related environment variables
    print("\n=== ENVIRONMENT VARIABLES ===")
    for key in os.environ:
        if "MYSQL" in key.upper() or "DATABASE" in key.upper():
            # Don't print passwords
            value = os.environ[key]
            if "password" in key.lower() or "pass" in key.lower():
                value = "***HIDDEN***"
            elif "@" in value:
                # Hide password in connection string
                value = value.split("@")[0].split(":")[:-1] + ["***"] + ["@"] + value.split("@")[1:]
                value = ":".join(value) if isinstance(value, list) else value
            print(f"{key} = {value}")
    print("============================\n")
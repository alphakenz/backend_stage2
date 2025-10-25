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
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Shutting down application...")
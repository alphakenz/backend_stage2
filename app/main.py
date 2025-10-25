"""
FastAPI application entry point
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.core.config import settings
from app.models.database import init_db
import logging

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


# Exception handlers to match brief JSON shapes
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        err = detail.get("error") or detail
        details = {k: v for k, v in detail.items() if k != "error"} or None
        body = {"error": err} if isinstance(err, str) else {"error": str(err)}
        if details:
            body["details"] = details
    else:
        body = {"error": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Convert Pydantic errors into brief-required shape
    errors = {}
    for err in exc.errors():
        loc = ".".join([str(x) for x in err.get("loc", [])])
        errors[loc] = err.get("msg")
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": errors})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
    logging.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Initialize DB safely at startup
    init_db()
"""
Main FastAPI application for the auth service
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .database import init_database, close_database
from .api.routers import auth_router, users_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Authentication and authorization microservice for the confectionery e-commerce platform",
    version=settings.app_version,
    docs_url=settings.docs_url if settings.show_docs else None,
    redoc_url=settings.redoc_url if settings.show_docs else None,
    openapi_url="/openapi.json" if settings.show_docs else None,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # CORS headers
    origin = request.headers.get("Origin")
    if origin in settings.allowed_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Content Security Policy
    if settings.is_production:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
    
    return response


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database
    await init_database()
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application...")
    
    # Close database connections
    await close_database()
    
    logger.info("Application shutdown completed")


# Include routers
app.include_router(auth_router)
app.include_router(users_router)


# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Check if the service is running and healthy"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the service status and basic information.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Service information",
    description="Get basic information about the auth service"
)
async def root():
    """
    Root endpoint with service information.
    
    Returns basic service information.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": "Authentication and authorization microservice",
        "docs_url": f"{settings.docs_url}" if settings.show_docs else None,
        "health_url": "/health"
    } 
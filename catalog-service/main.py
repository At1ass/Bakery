from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.exceptions import RequestValidationError

from app.api.routers import products, health
from app.core.config import settings
from app.core.exceptions import (
    CatalogServiceException,
    catalog_service_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.db.mongodb import init_db

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Catalog Service",
    description="Product catalog management service",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add custom exception handlers
app.add_exception_handler(CatalogServiceException, catalog_service_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, tags=["products"])
app.include_router(health.router, tags=["health"])

@app.on_event("startup")
async def startup_db_client():
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    # MongoDB motor client handles cleanup automatically
    pass

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Catalog Service",
        "version": "1.0.0",
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
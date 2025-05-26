from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging

from ...schemas.order import HealthResponse
from ...core.config import settings
from ...db.mongodb import get_database

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the order service and its dependencies"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint that verifies:
    - Service is running
    - Database connectivity
    - Basic service information
    """
    try:
        # Test database connection
        db = await get_database()
        await db.command('ping')
        
        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Database connection failed"
            }
        )


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 if service is ready to handle requests.
    """
    try:
        # Test database connection
        db = await get_database()
        await db.command('ping')
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get(
    "/live",
    summary="Liveness check", 
    description="Check if the service is alive"
)
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()} 
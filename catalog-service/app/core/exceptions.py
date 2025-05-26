"""
Custom exceptions and error handlers for the catalog service.
Following FastAPI best practices for error handling.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class CatalogServiceException(Exception):
    """Base exception for catalog service"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ProductNotFoundException(CatalogServiceException):
    """Exception raised when a product is not found"""
    def __init__(self, product_id: str):
        message = f"Product with ID '{product_id}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ProductAlreadyExistsException(CatalogServiceException):
    """Exception raised when trying to create a product that already exists"""
    def __init__(self, product_name: str):
        message = f"Product with name '{product_name}' already exists"
        super().__init__(message, status.HTTP_409_CONFLICT)


class InvalidProductDataException(CatalogServiceException):
    """Exception raised when product data is invalid"""
    def __init__(self, message: str):
        super().__init__(f"Invalid product data: {message}", status.HTTP_400_BAD_REQUEST)


class DatabaseConnectionException(CatalogServiceException):
    """Exception raised when database connection fails"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class InsufficientPermissionsException(CatalogServiceException):
    """Exception raised when user lacks required permissions"""
    def __init__(self, action: str):
        message = f"Insufficient permissions to {action}"
        super().__init__(message, status.HTTP_403_FORBIDDEN)


# Error handlers
async def catalog_service_exception_handler(request: Request, exc: CatalogServiceException):
    """Handle custom catalog service exceptions"""
    logger.error(f"CatalogServiceException: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "CatalogServiceError",
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    ) 
"""
API layer for the auth service
"""

from .dependencies import get_current_user, get_auth_service
from .routers import auth_router, users_router

__all__ = [
    "get_current_user",
    "get_auth_service", 
    "auth_router",
    "users_router",
] 
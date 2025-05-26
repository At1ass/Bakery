"""
FastAPI dependencies for dependency injection
"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from ..models import UserOut
from ..services import AuthService

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Service instances (could be made singleton if needed)
_auth_service: AuthService = None


def get_auth_service() -> AuthService:
    """
    Get the authentication service instance.
    
    Returns:
        AuthService: The authentication service
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserOut:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        token: The JWT access token
        auth_service: The authentication service
        
    Returns:
        UserOut: The current user data
        
    Raises:
        HTTPException: If authentication fails
    """
    return await auth_service.get_current_user(token) 
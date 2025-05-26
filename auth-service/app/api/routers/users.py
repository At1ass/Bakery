"""
User management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...models import UserOut
from ...services import AuthService
from ..dependencies import get_current_user, get_auth_service

# Router configuration
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "User not found"},
    }
)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
    description="Get the profile information of the currently authenticated user"
)
async def get_current_user_profile(
    current_user: UserOut = Depends(get_current_user)
) -> UserOut:
    """
    Get the current user's profile information.
    
    Returns the authenticated user's profile data.
    """
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get user by ID",
    description="Get user information by user ID (requires authentication)"
)
async def get_user_by_id(
    user_id: str,
    current_user: UserOut = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserOut:
    """
    Get user information by ID.
    
    - **user_id**: The user's unique identifier
    
    Returns the user's profile information if found.
    """
    # Users can only access their own profile or admins can access any profile
    if current_user.id != user_id and current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's information"
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get(
    "/",
    response_model=UserOut,
    summary="Health check for users endpoint",
    description="Simple health check endpoint for the users router"
)
async def users_health_check() -> dict:
    """
    Health check endpoint for users router.
    
    Returns a simple status message.
    """
    return {"status": "Users service is healthy", "service": "auth-service"} 
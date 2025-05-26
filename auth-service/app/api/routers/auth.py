"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...models import UserIn, UserOut, Token, RefreshToken
from ...services import AuthService
from ...core.config import settings
from ..dependencies import get_auth_service

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Router configuration
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    }
)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password validation"
)
@limiter.limit(settings.rate_limit_register)
async def register(
    request: Request,
    user_data: UserIn,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserOut:
    """
    Register a new user account.
    
    - **email**: Valid email address (will be converted to lowercase)
    - **password**: Strong password (min 12 chars, uppercase, lowercase, number, special char)
    - **role**: User role (Customer, Seller, or Admin)
    
    Returns the created user data without sensitive information.
    """
    return await auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return access and refresh tokens"
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Authenticate user and return JWT tokens.
    
    - **username**: User's email address
    - **password**: User's password
    
    Returns access token, refresh token, and user role.
    Access token expires in 30 minutes, refresh token in 7 days.
    """
    return await auth_service.authenticate_user(form_data)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange refresh token for new access and refresh tokens"
)
@limiter.limit(settings.rate_limit_refresh)
async def refresh_token(
    request: Request,
    refresh_data: RefreshToken,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new access token and refresh token.
    """
    return await auth_service.refresh_access_token(refresh_data.refresh_token) 
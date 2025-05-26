"""
Authentication service containing business logic
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..models import UserIn, UserOut, UserInDB, Token
from ..core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token
)
from ..core.config import settings
from ..core.logging import get_logger
from ..database.repositories import UserRepository

logger = get_logger(__name__)


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    async def register_user(self, user_data: UserIn) -> UserOut:
        """
        Register a new user.
        
        Args:
            user_data: The user registration data
            
        Returns:
            UserOut: The created user data
            
        Raises:
            HTTPException: If registration fails
        """
        # Check if user already exists
        existing_user = await self.user_repository.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user in database
        user_in_db = UserInDB(
            email=user_data.email,
            role=user_data.role,
            hashed_password=get_password_hash(user_data.password),
            created_at=datetime.utcnow()
        )
        
        try:
            created_user = await self.user_repository.create_user(user_in_db)
            logger.info(f"User registered successfully: {created_user.email}")
            return created_user
            
        except Exception as e:
            logger.error(f"Failed to register user {user_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
    
    async def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> Token:
        """
        Authenticate a user and return tokens.
        
        Args:
            form_data: The login form data
            
        Returns:
            Token: The authentication tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        # Get user from database
        user = await self.user_repository.get_user_by_email(form_data.username)
        
        if not user:
            await self._handle_failed_login(form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked until {user.locked_until}"
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            await self._handle_failed_login(form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Reset failed login attempts on successful login
        await self.user_repository.reset_failed_login_attempts(user.email)
        
        # Update last login
        await self.user_repository.update_last_login(user.id)
        
        # Create tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"User authenticated successfully: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            role=user.role,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Token: New authentication tokens
            
        Raises:
            HTTPException: If refresh fails
        """
        # Verify refresh token
        try:
            payload = verify_token(refresh_token, "refresh")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = await self.user_repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            role=user.role,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def get_current_user(self, token: str) -> UserOut:
        """
        Get the current user from an access token.
        
        Args:
            token: The access token
            
        Returns:
            UserOut: The current user data
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify access token
        try:
            payload = verify_token(token, "access")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Optional[UserOut]: The user data if found
        """
        return await self.user_repository.get_user_by_id(user_id)
    
    async def _handle_failed_login(self, email: str) -> None:
        """
        Handle failed login attempt by incrementing counter and potentially locking account.
        
        Args:
            email: The user's email address
        """
        # Increment failed login attempts
        await self.user_repository.increment_failed_login_attempts(email)
        
        # Get updated user to check failed attempts
        user = await self.user_repository.get_user_by_email(email)
        if user and user.failed_login_attempts >= 5:
            # Lock account for 30 minutes after 5 failed attempts
            lock_until = datetime.utcnow() + timedelta(minutes=30)
            await self.user_repository.lock_user_account(email, lock_until)
            logger.warning(f"Account locked due to failed login attempts: {email}")
        
        logger.warning(f"Failed login attempt for: {email}") 
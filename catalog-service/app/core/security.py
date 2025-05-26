from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from datetime import datetime
import logging

from .config import settings

# Setup logger
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Debug: Print JWT secret info on module load
print(f"DEBUG: JWT secret loaded, length: {len(settings.jwt_secret)}")
print(f"DEBUG: JWT algorithm: {settings.jwt_algorithm}")

class TokenPayload(BaseModel):
    """Model for JWT token payload validation"""
    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


async def verify_token(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return user data
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Extract token from authorization header
        scheme = authorization.scheme
        token = authorization.credentials
        
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
        # Decode JWT token
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret, 
                algorithms=[settings.jwt_algorithm]
            )
            
            # Extract user data from payload
            user_data = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "exp": payload.get("exp")
            }
            
            # Validate required fields
            if not user_data["user_id"] or not user_data["email"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        ) 
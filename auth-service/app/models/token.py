"""
Token data models
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """Token payload data model"""
    uid: Optional[str] = Field(None, description="User ID")
    email: Optional[str] = Field(None, description="User email")
    role: Optional[str] = Field(None, description="User role")
    exp: Optional[datetime] = Field(None, description="Token expiration time")
    iat: Optional[datetime] = Field(None, description="Token issued at time")
    type: Optional[Literal["access", "refresh"]] = Field(None, description="Token type")
    jti: Optional[str] = Field(None, description="JWT ID for token revocation")


class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: Literal["bearer"] = Field("bearer", description="Token type (always 'bearer')")
    role: Literal["Customer", "Seller", "Admin"] = Field(..., description="User's role")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "role": "Customer",
                "expires_in": 1800
            }
        }


class RefreshToken(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="JWT refresh token to exchange for new access token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        } 
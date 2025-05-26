"""
User data models
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, validator

from ..core.config import settings


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    role: Literal["Customer", "Seller", "Admin"] = Field("Customer", description="User's role")

    @validator('email')
    def email_must_be_lowercase(cls, v):
        """Ensure email is lowercase"""
        return v.lower()


class UserIn(UserBase):
    """User input model for registration"""
    password: str = Field(
        ...,
        min_length=12,
        description="User's password (min 12 chars, must include uppercase, lowercase, number, and special char)"
    )

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        import re
        
        if len(v) < settings.min_password_length:
            raise ValueError(f'Password must be at least {settings.min_password_length} characters long')
        
        if not re.match(settings.password_pattern, v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v


class UserOut(UserBase):
    """User output model for API responses"""
    id: str = Field(..., description="User's unique identifier")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last successful login timestamp")
    is_active: bool = Field(True, description="Whether the user account is active")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "role": "Customer",
                "created_at": "2023-01-01T00:00:00",
                "last_login": "2023-01-02T00:00:00",
                "is_active": True
            }
        }


class UserInDB(UserBase):
    """User model for database storage"""
    id: Optional[str] = Field(None, description="User's unique identifier")
    hashed_password: str = Field(..., description="User's hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last successful login timestamp")
    is_active: bool = Field(True, description="Whether the user account is active")
    failed_login_attempts: int = Field(0, description="Number of consecutive failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiration time")

    class Config:
        # Allow population by field name for MongoDB compatibility
        allow_population_by_field_name = True 
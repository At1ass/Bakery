from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., pattern="^(Customer|Seller|Admin)$", description="User's role")

    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class UserIn(UserBase):
    password: str = Field(
        ...,
        min_length=12,
        description="User's password (min 12 chars, must include uppercase, lowercase, number, and special char)"
    )

    @validator('password')
    def password_strength(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$', v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v

class UserOut(UserBase):
    id: str = Field(..., description="User's unique identifier")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last successful login timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "role": "user"
            }
        }

class TokenData(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    type: Optional[str] = Field(None, pattern="^(access|refresh)$")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", pattern="^bearer$", description="Token type (always 'bearer')")
    role: str = Field(..., pattern="^(Customer|Seller|Admin)$", description="User's role")

class RefreshToken(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token to exchange for new access token")

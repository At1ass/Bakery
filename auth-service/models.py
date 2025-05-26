from pydantic import BaseModel, EmailStr, Field, validator
from typing import Literal
import re

class UserIn(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (min 8 characters, must include uppercase, lowercase, number, and special character)"
    )
    role: Literal["user", "seller"] = Field(
        default="user",
        description="User's role in the system"
    )

    @validator('password')
    def validate_password(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number and one special character'
            )
        return v

class UserOut(BaseModel):
    id: str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., description="User's role in the system")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "role": "user"
            }
        }

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (bearer)")
    role: str = Field(..., description="User's role")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "role": "user"
            }
        }

class TokenData(BaseModel):
    uid: str = Field(..., description="User ID from token")

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class UserIn(BaseModel):
    email: EmailStr
    password: str
    role: Literal["user", "seller"] = "user"  # Default role is user

class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str  # Include role in token response

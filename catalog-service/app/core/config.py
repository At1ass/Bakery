import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    app_name: str = "Catalog Service"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database settings
    mongo_url: str = "mongodb://mongo:27017"
    database_name: str = "confectionery"
    mongo_max_pool_size: int = 100
    mongo_min_pool_size: int = 10
    
    # Security settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    
    # CORS settings - will be parsed from string if needed
    allowed_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001,https://localhost:3002"
    
    # Rate limiting
    rate_limit_per_minute: int = 30
    
    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        return v
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins as a list"""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
        return self.allowed_origins
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
        env_nested_delimiter="__"
    )


# Create settings instance
settings = Settings() 
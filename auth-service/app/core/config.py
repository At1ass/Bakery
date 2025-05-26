"""
Configuration settings for the auth service
"""

import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application settings
    app_name: str = Field("Auth Service", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    environment: str = Field("development", description="Environment (development/production)")
    debug: bool = Field(False, description="Debug mode")
    
    # API settings
    api_prefix: str = Field("/api/v1", description="API prefix")
    docs_url: str = Field("/docs", description="Documentation URL")
    redoc_url: str = Field("/redoc", description="ReDoc URL")
    
    # Security settings
    jwt_secret: str = Field(..., description="JWT secret key", min_length=32)
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(7, description="Refresh token expiration in days")
    
    # Password settings
    min_password_length: int = Field(12, description="Minimum password length")
    password_pattern: str = Field(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$',
        description="Password validation pattern"
    )
    
    # Database settings
    mongo_uri: str = Field("mongodb://mongo:27017", description="MongoDB connection URI")
    mongo_db_name: str = Field("confectionery", description="MongoDB database name")
    mongo_max_pool_size: int = Field(100, description="MongoDB max pool size")
    mongo_min_pool_size: int = Field(10, description="MongoDB min pool size")
    mongo_max_retries: int = Field(5, description="MongoDB connection max retries")
    mongo_retry_delay: int = Field(1, description="MongoDB retry delay in seconds")
    
    # CORS settings
    allowed_origins: str = Field(
        "http://localhost:3001,https://localhost:3002",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Rate limiting settings
    rate_limit_login: str = Field("5/minute", description="Login rate limit")
    rate_limit_register: str = Field("3/minute", description="Register rate limit")
    rate_limit_refresh: str = Field("5/minute", description="Refresh token rate limit")
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if v not in ['development', 'production', 'testing']:
            raise ValueError('Environment must be development, production, or testing')
        return v
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins string into a list"""
        return [origin.strip() for origin in self.allowed_origins.split(',')]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def show_docs(self) -> bool:
        return not self.is_production
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "AUTH_",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings() 
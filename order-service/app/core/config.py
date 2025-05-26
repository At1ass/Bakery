from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = Field(default="Order Service", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    docs_url: Optional[str] = Field(default="/docs", env="DOCS_URL")
    redoc_url: Optional[str] = Field(default="/redoc", env="REDOC_URL")
    
    # Security settings
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Database settings
    mongo_url: str = Field(default="mongodb://mongo:27017", env="MONGO_URI")
    database_name: str = Field(default="confectionery", env="DATABASE_NAME")
    mongo_max_pool_size: int = Field(default=100, env="MONGO_MAX_POOL_SIZE")
    mongo_min_pool_size: int = Field(default=10, env="MONGO_MIN_POOL_SIZE")
    
    # External services
    auth_service_url: str = Field(default="http://auth:8000", env="AUTH_SERVICE_URL")
    catalog_service_url: str = Field(default="http://catalog:8000", env="CATALOG_SERVICE_URL")
    
    # CORS settings
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,https://localhost:3002",
        env="ALLOWED_ORIGINS"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins as a list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def get_docs_url(self) -> Optional[str]:
        """Get docs URL, None in production"""
        return None if self.is_production() else self.docs_url
    
    def get_redoc_url(self) -> Optional[str]:
        """Get redoc URL, None in production"""
        return None if self.is_production() else self.redoc_url

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 
"""
Core Application Configuration

This module contains the core configuration settings for the SAFE-BMAD API application.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""

    # Environment Configuration
    environment: str = "development"
    environment_name: str = "Development Environment"
    debug: bool = True

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    reload: bool = True
    api_prefix: str = "/api/v1"

    # Security Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Database Configuration
    database_url: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "safe_dev"
    db_user: str = "safe_user"
    db_password: str = "safe_password"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_echo: bool = False

    # Redis Configuration
    redis_url: str
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_pool_size: int = 10
    redis_max_connections: int = 50

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/app.log"
    log_max_size: str = "10MB"
    log_backup_count: int = 5

    # AI/ML Configuration
    ai_model_name: str = "deepseek-chat"
    ai_model_base_url: str = "http://localhost:8000/v1"
    ai_api_key: Optional[str] = None
    ai_model_temperature: float = 0.7
    ai_model_max_tokens: int = 2000
    ai_model_timeout: int = 30

    # AutoGen Configuration
    autogen_max_worker_agents: int = 5
    autogen_max_round_trips: int = 10
    autogen_enable_code_execution: bool = True
    autogen_enable_docker: bool = False

    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    performance_monitoring: bool = True

    # Pagination Configuration
    default_page_size: int = 20
    max_page_size: int = 100

    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    allowed_file_types: List[str] = [".json", ".csv", ".txt", ".pdf", ".doc", ".docx"]

    # Email Configuration (for notifications)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True

    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour default
    cache_prefix: str = "safe_bmad"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_environments = ["development", "testing", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level setting"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://'")
        return v

    @validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with 'redis://'")
        return v

    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate secret key length"""
        if len(v) < 32:
            logger.warning("SECRET_KEY should be at least 32 characters long")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"

    @property
    def database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_recycle": self.db_pool_recycle,
            "echo": self.db_echo or self.debug
        }

    @property
    def redis_config(self) -> dict:
        """Get Redis configuration dictionary"""
        config = {
            "url": self.redis_url,
            "max_connections": self.redis_max_connections,
            "retry_on_timeout": True,
            "decode_responses": True
        }
        if self.redis_password:
            config["password"] = self.redis_password
        return config

    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        if isinstance(self.cors_origins, str):
            # Handle comma-separated string
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins

    def get_database_async_url(self) -> str:
        """Get async database URL for SQLAlchemy"""
        database_url = self.database_url
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://")
        return database_url


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings instance
    Loads settings from environment variables and .env file
    """
    global _settings

    if _settings is None:
        try:
            _settings = Settings()
            logger.info(f"Settings loaded for environment: {_settings.environment}")
        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}")
            raise

    return _settings


def reload_settings():
    """
    Reload settings instance
    Useful for testing or when environment variables change
    """
    global _settings
    _settings = None
    return get_settings()
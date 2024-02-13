"""
Configuration management for Pulse Trading Platform
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app config
    PROJECT_NAME: str = "Pulse Trading Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://pulse:pulse_password@localhost:5432/pulse"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis Configuration  
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Satellite Data APIs
    PLANET_API_KEY: Optional[str] = None
    MAXAR_API_KEY: Optional[str] = None
    LANDSAT_API_KEY: Optional[str] = None
    GOOGLE_EARTH_ENGINE_KEY: Optional[str] = None
    
    # Financial Data APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    IEX_CLOUD_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    QUANDL_API_KEY: Optional[str] = None
    
    # Trading Configuration
    TRADING_MODE: str = "paper"  # paper, live
    MAX_POSITION_SIZE: float = 0.02  # 2% of portfolio
    MAX_SECTOR_EXPOSURE: float = 0.10  # 10% per sector
    STOP_LOSS_MULTIPLIER: float = 2.0  # 2x ATR
    MAX_DAILY_LOSS: float = 0.01  # 1% of portfolio
    
    # ML Model Configuration
    SATELLITE_MODEL_PATH: str = "models/satellite_segmentation.h5"
    SIGNAL_MODEL_PATH: str = "models/trading_signals.pkl"
    BATCH_SIZE: int = 16
    GPU_ENABLED: bool = True
    
    # Background Task Configuration
    SATELLITE_PROCESSING_INTERVAL: int = 300  # 5 minutes
    MARKET_DATA_UPDATE_INTERVAL: int = 60    # 1 minute  
    SIGNAL_GENERATION_INTERVAL: int = 900    # 15 minutes
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Monitoring & Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090
    
    # File Storage
    DATA_DIRECTORY: Path = Path("data")
    SATELLITE_IMAGE_DIRECTORY: Path = Path("data/satellite_images") 
    MODEL_DIRECTORY: Path = Path("models")
    LOG_DIRECTORY: Path = Path("logs")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.DATA_DIRECTORY.mkdir(exist_ok=True)
settings.SATELLITE_IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIRECTORY.mkdir(exist_ok=True)
settings.LOG_DIRECTORY.mkdir(exist_ok=True)
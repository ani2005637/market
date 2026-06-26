import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Liquidity AI API"
    API_V1_STR: str = "/api"
    
    # Database
    # Default to sqlite local database for MVP, but can be configured to PostgreSQL via env
    DATABASE_URL: str = "sqlite:///./smart_liquidity.db"
    
    # Security
    SECRET_KEY: str = "supersecretkeychangeinproduction123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # ML Models path
    MODEL_DIR: str = "./ml_models"
    MODEL_NAME: str = "xgboost_setup_classifier.joblib"
    SCALER_NAME: str = "robust_scaler.joblib"
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60 per minute"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure model directory exists
os.makedirs(settings.MODEL_DIR, exist_ok=True)

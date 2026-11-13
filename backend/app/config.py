import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AssetTrack"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Secret Key for JWT
    SECRET_KEY: str = "assettrack-enterprise-super-secret-key-change-in-production-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./assettrack.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Uploads / Storage
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "./media")
    QR_DIR: str = os.getenv("QR_DIR", "./media/qr_codes")
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./media/reports")
    
    # Seed Configuration
    SEED_ADMIN_EMAIL: str = "admin@assettrack.io"
    SEED_ADMIN_PASSWORD: str = "Admin123!Secure"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

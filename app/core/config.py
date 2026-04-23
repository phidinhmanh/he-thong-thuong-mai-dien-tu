from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Amazon Clone API"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./amazon_clone.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-xyz123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
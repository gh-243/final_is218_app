# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database settings (keeping your existing default)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_REFRESH_SECRET_KEY: str = "your-refresh-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: List[str] = ["*"]
    
    # Redis (optional, for token blacklisting)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # OpenAI API Key (optional, for AI Queue Insights feature)
    # If not provided, the system will use rule-based fallback analysis
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default model for cost-effectiveness
    OPENAI_MAX_TOKENS: int = 500  # Limit response length for insights
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings instance
settings = Settings()

# Optional: Add cached settings getter
@lru_cache()
def get_settings() -> Settings:
    return Settings()
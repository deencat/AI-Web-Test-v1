from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Web Test"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    # OpenRouter (for Sprint 2 - Test Generation)
    OPENROUTER_API_KEY: str | None = None  # Optional for now
    OPENROUTER_MODEL: str = "mistralai/mixtral-8x7b-instruct"  # Default: Free, high-quality model
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


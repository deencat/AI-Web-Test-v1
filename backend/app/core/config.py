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
    
    # Google AI Studio (Direct API - FREE alternative to OpenRouter)
    USE_GOOGLE_DIRECT: bool = False  # Set to True to use Google API directly
    GOOGLE_API_KEY: str | None = None  # Get from: https://aistudio.google.com/app/apikey
    GOOGLE_MODEL: str = "gemini-1.5-flash"  # gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp
    
    # Cerebras (Fast inference - https://cerebras.ai/)
    USE_CEREBRAS: bool = False  # Set to True to use Cerebras
    CEREBRAS_API_KEY: str | None = None  # Get from: https://cloud.cerebras.ai/
    CEREBRAS_MODEL: str = "llama3.1-8b"  # llama3.1-8b, llama3.1-70b
    
    # Azure OpenAI (Company-provided)
    AZURE_OPENAI_API_KEY: str | None = None  # Company Azure OpenAI API key
    AZURE_OPENAI_ENDPOINT: str = "https://chatgpt-uat.openai.azure.com/openai/v1"
    AZURE_OPENAI_MODEL: str = "ChatGPT-UAT"  # Deployment name
    
    # Model Provider Selection (new unified approach)
    # Options: "openrouter", "google", "cerebras", "azure"
    MODEL_PROVIDER: str = "openrouter"  # Default provider
    
    # OpenAI API compatibility (for Stagehand/LiteLLM)
    # These can be set to use OpenRouter as a drop-in replacement
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    
    # Queue System (for Sprint 3 Day 2)
    MAX_CONCURRENT_EXECUTIONS: int = 5  # Maximum concurrent test executions
    QUEUE_CHECK_INTERVAL: int = 2  # How often to check queue (seconds)
    EXECUTION_TIMEOUT: int = 300  # Execution timeout (seconds)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env without errors


settings = Settings()


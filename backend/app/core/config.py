from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"  # Sprint 10: Agent Workflow API
    PROJECT_NAME: str = "Agentic QA"
    
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
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_MODEL: str = "ChatGPT-UAT"  # Deployment name

    # Azure OpenAI — gpt-5.2 dedicated deployment (hutch resource, eastus2)
    AZURE_OPENAI_GPT52_ENDPOINT: str | None = None   # https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com/
    AZURE_OPENAI_GPT52_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_GPT52_API_KEY: str | None = None    # Defaults to AZURE_OPENAI_API_KEY when not set
    
    # Model Provider Selection (new unified approach)
    # Options: "openrouter", "google", "cerebras", "azure", "local_vllm"
    MODEL_PROVIDER: str = "openrouter"  # Default provider
    
    # OpenAI API compatibility (for Stagehand/LiteLLM)
    # These can be set to use OpenRouter as a drop-in replacement
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    
    # Queue System (for Sprint 3 Day 2)
    MAX_CONCURRENT_EXECUTIONS: int = 5  # Maximum concurrent test executions
    QUEUE_CHECK_INTERVAL: int = 2  # How often to check queue (seconds)
    EXECUTION_TIMEOUT: int = 300  # Execution timeout (seconds)

    # API v2: AnalysisAgent real-time test execution (Phase3 Architecture)
    # When True, POST /generate-tests and POST /analysis run critical scenarios for scoring.
    ENABLE_ANALYSIS_REALTIME_EXECUTION: bool = True

    # Server: when True, start_server.py writes logs to backend/logs/ (in addition to console).
    ENABLE_SERVER_FILE_LOGGING: bool = False

    # After ObservationAgent: write playwright_flow_recording.json + flow_steps.json under artifacts/flow_recordings/{workflow_id}/
    FLOW_RECORDINGS_ENABLED: bool = True
    # Optional override; relative paths are resolved from backend root. Env FLOW_RECORDINGS_DIR also supported.
    FLOW_RECORDINGS_DIR: str | None = None

    # Sprint 10.10: IMAP Email OTP polling
    EMAIL_OTP_POLL_TIMEOUT: int = 60    # seconds to wait for OTP email
    EMAIL_OTP_POLL_INTERVAL: int = 3    # seconds between polls

    # Sprint 10.13: Local vLLM / on-premises OpenAI-compatible models
    # Each model has its own endpoint; no auth key required by default (set to "local" or a real key)
    LOCAL_VLLM_GPT_OSS_20B_ENDPOINT: str = "http://192.168.206.190:8000/openai--gpt-oss-20b/v1"
    LOCAL_VLLM_QWEN3_35B_ENDPOINT: str = "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1"
    LOCAL_VLLM_DEEPSEEK_ENDPOINT: str = "http://192.168.206.164:1235/v1"
    LOCAL_VLLM_API_KEY: str = "local"   # shared placeholder; vLLM ignores auth by default

    # ReqIQ integration (server-to-server, credentials never exposed to browser)
    REQIQ_URL: str = "http://localhost:3001"
    REQIQ_SERVICE_EMAIL: str | None = None
    REQIQ_SERVICE_PASSWORD: str | None = None
    REQIQ_TENANT_ID: str | None = None
    REQIQ_PROJECT_ID_VOUCHER_PLAN: str | None = None

    # MCP Server (Hermes Agent integration — never exposed to browser)
    AWT_MCP_SECRET: str | None = None          # shared secret Hermes sends in Authorization header
    AWT_MCP_PORT: int = 8001                   # port the MCP server listens on
    AWT_BASE_URL: str = "http://localhost:8000/api/v1"  # internal REST API base
    AWT_SERVICE_USERNAME: str | None = None     # service account username for internal REST calls
    AWT_SERVICE_PASSWORD: str | None = None    # service account password

    # Hermes Telegram trigger (H2 — "Generate via Hermes" button in UI)
    # Bot token from BotFather; same token as TELEGRAM_BOT_TOKEN in ~/.hermes/.env on Node 1
    TELEGRAM_BOT_TOKEN: str | None = None
    # DM chat ID between your Telegram user account and the qa-manager bot
    QA_MANAGER_TELEGRAM_CHAT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Allow extra fields in .env without errors
    )


settings = Settings()


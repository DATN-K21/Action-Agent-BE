from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LlmProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Debug mode
    DEBUG_AGENT: bool = False
    DEBUG_SERVER: bool = False
    DEBUG_SQLALCHEMY: bool = False

    # Logging
    LOGGING_LOG_LEVEL: str = "INFO"

    # User Agent for web requests
    USER_AGENT: str = "Action-LLM-AI-Service/1.0 (Educational Project)"

    # LLM
    OPENAI_PROVIDER: LlmProvider = LlmProvider.OPENAI
    ANTHROPIC_PROVIDER: LlmProvider = LlmProvider.ANTHROPIC

    LLM_BASIC_MODEL: str = "gpt-4o-mini"
    BASIC_MODEL_TEMPERATURE: float = 0.5
    BASIC_MODEL_CONTEXT_RATIO: float = 0.2

    LLM_REASONING_MODEL: str = "claude-3-5-haiku-20241022"
    REASONING_MODEL_TEMPERATURE: float = 0
    REASONING_MODEL_CONTEXT_RATIO: float = 0.1

    LLM_VISION_MODEL: str = "gpt-4o-mini"
    VISION_MODEL_TEMPERATURE: float = 0.5
    VISION_MODEL_CONTEXT_RATIO: float = 0.2

    # Suggestion service LLM settings
    LLM_SUGGESTION_MODEL: str = "gpt-4.1-mini"
    SUGGESTION_MODEL_TEMPERATURE: float = 0.3
    SUGGESTION_MODEL_MAX_TOKENS: int = 5000

    OPENAI_API_KEY: str = "<YOUR-API-KEY>"
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"

    ANTHROPIC_API_KEY: str = "<YOUR-API-KEY>"
    ANTHROPIC_API_BASE_URL: str = "https://api.anthropic.com"

    DEFAULT_CONTEXT_LIMIT: int = 100000  # Default context limit in tokens
    DEFAULT_CONTEXT_RATIO: float = 0.2  # Ratio of context to response tokens

    # Embedding
    EMBEDDING_PROVIDER: str = "openai"

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai-database"

    # Tool
    TOOL_TAVILY_API_KEY: str = "<your-api-key>"

    # Composio
    COMPOSIO_LOGGING_LEVEL: str = "debug"
    COMPOSIO_API_KEY: str = "<your-api-key>"
    COMPOSIO_REDIRECT_URL: str = "http://localhost:15200/callback/extension"

    # Frontend service
    FRONTEND_REDIRECT_URL: str = "http://localhost:3000/callback/extension"

    # Security keys
    SECRET_KEY: str = "<secret-key>"
    MODEL_PROVIDER_ENCRYPTION_KEY: str = "<encryption-key>"

    # Vectorstore settings
    PGVECTOR_COLLECTION: str = "<collection-name>"

    # Graph settings
    RECURSION_LIMIT: int = 25

    # Upload settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB

    # Memory and Cache settings
    SYSTEM_MEMORY_THRESHOLD: float = 92.0  # System memory threshold percentage
    CACHE_MEMORY_THRESHOLD: float = 0.92  # Cache memory threshold ratio
    CACHE_STARTUP_GRACE_PERIOD: float = 60.0  # Startup grace period in seconds
    CACHE_CLEANUP_RATIO: float = 0.2  # Default cleanup ratio
    CACHE_ENABLE_MEMORY_LOGGING: bool = True  # Enable detailed memory usage logging during cache checks
    CACHE_DETAILED_LOGGING_INTERVAL: float = 300.0  # Interval for detailed memory reports in seconds (5 minutes)
    CACHE_MEMORY_CHECK_INTERVAL: float = 120.0  # Interval for memory checks in seconds
    CACHE_TTL_SECONDS: float = 3600.0  # Default TTL for cache entries in seconds (1 hour)

    # Cache for streaming connections
    STREAMING_CONNECTIONS_CACHE_MAX_ENTRIES: int = 1000  # Maximum concurrent
    STREAMING_CONNECTIONS_CACHE_MAX_MEMORY_MB: float = 64.0  # 64MB for connection tracking

    # Cache for tools
    TOOLS_CACHE_MAX_ENTRIES: int = 1000  # Maximum number of cached
    TOOLS_CACHE_MAX_MEMORY_MB: float = 512.0  # 512MB for tool tracking

    # Cache for extension services
    EXTENSION_SERVICES_CACHE_MAX_ENTRIES: int = 400  # Maximum number of cached extension services
    EXTENSION_SERVICES_CACHE_MAX_MEMORY_MB: float = 256.0  #

    # Sets the number of processors
    MAX_WORKERS: int = 1

    # Celery settings
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Embedding model. See the list of supported models: https://qdrant.github.io/fastembed/examples/Supported_Models/
    DENSE_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    SPARSE_EMBEDDING_MODEL: str = "prithivida/Splade_PP_en_v1"
    FASTEMBED_CACHE_PATH: str = "./fastembed_cache"

    # Extension service settings
    EXTENSION_SERVICE_URL: str = "http://localhost:15300"

    # Protected names
    PROTECTED_NAMES: list[str] = ["user", "ignore", "error"]

    @property
    def POSTGRES_URL_PATH(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache()
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

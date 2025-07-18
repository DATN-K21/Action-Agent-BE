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
    BASIC_MODEL_PROVIDER: LlmProvider = LlmProvider.OPENAI
    REASONING_MODEL_PROVIDER: LlmProvider = LlmProvider.DEEPSEEK
    VISION_MODEL_PROVIDER: LlmProvider = LlmProvider.OPENAI
    SUGGESTION_MODEL_PROVIDER: LlmProvider = LlmProvider.OPENAI

    BASIC_MODEL: str = "gpt-4o-mini"
    BASIC_MODEL_TEMPERATURE: float = 0.5
    BASIC_MODEL_CONTEXT_RATIO: float = 0.05
    BASIC_MODEL_API_KEY: str = "<YOUR-API-KEY>"
    BASIC_MODEL_API_BASE_URL: str = "https://api.openai.com/v1"

    REASONING_MODEL: str = "deepseek-chat"
    REASONING_MODEL_TEMPERATURE: float = 0
    REASONING_MODEL_CONTEXT_RATIO: float = 0.2
    REASONING_MODEL_API_KEY: str = "<YOUR-API-KEY>"
    REASONING_MODEL_API_BASE_URL: str = "https://api.deepseek.com"

    VISION_MODEL: str = "gpt-4o-mini"
    VISION_MODEL_TEMPERATURE: float = 0.5
    VISION_MODEL_CONTEXT_RATIO: float = 0.2
    VISION_MODEL_API_KEY: str = "<YOUR-API-KEY>"
    VISION_MODEL_API_BASE_URL: str = "https://api.openai.com/v1"

    # Suggestion service LLM settings
    SUGGESTION_MODEL: str = "gpt-4o-mini"
    SUGGESTION_MODEL_TEMPERATURE: float = 0.3
    SUGGESTION_MODEL_MAX_TOKENS: int = 5000
    SUGGESTION_MODEL_API_KEY: str = "<YOUR-API-KEY>"
    SUGGESTION_MODEL_API_BASE_URL: str = "https://api.openai.com/v1"

    OPENAI_API_KEY: str = "<YOUR-API-KEY>"
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"

    ANTHROPIC_API_KEY: str = "<YOUR-API-KEY>"
    ANTHROPIC_API_BASE_URL: str = "https://api.anthropic.com"

    DEEPSEEK_API_KEY: str = "<YOUR-API-KEY>"
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.com"

    DEFAULT_CONTEXT_LIMIT: int = 100000  # Default context limit in tokens
    DEFAULT_CONTEXT_RATIO: float = 0.2  # Ratio of context to response tokens

    # Database
    POSTGRES_URL_PATH: str = "postgres:123456@localhost:5432/ai-database"
    POSTGRES_SCHEMA: str = "aiservice"

    # Tools
    TOOL_TAVILY_API_KEY: str = "<your-api-key>"

    # Composio
    COMPOSIO_LOGGING_LEVEL: str = "debug"
    COMPOSIO_API_KEY: str = "<your-api-key>"
    COMPOSIO_REDIRECT_URL: str = "http://localhost:15200/callback/extension"

    # Security keys
    SECRET_KEY: str = "<secret-key>"
    MODEL_PROVIDER_ENCRYPTION_KEY: str = "<encryption-key>"

    # Graph settings
    RECURSION_LIMIT: int = 25

    # Cache settings
    MAX_PERSONAL_TOOLS_PER_USER: int = 500
    MAX_CACHED_USERS: int = 200
    MAX_CACHED_EXTENSION_SERVICES: int = 400
    MAX_CACHED_MCP_USERS: int = 100
    MAX_MCP_CLIENT_INSTANCES_PER_USER: int = 20

    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 50 * 1024 * 1024  # 50 MB
    AZURE_BLOB_CONNECTION_STRING: str = "<your-connection-string>"
    AZURE_BLOB_CONTAINER_NAME: str = "uploadingdev"

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
    RABBITMQ_URL: str = "amqp://root:root@localhost:5672/"
    REDIS_URL: str = "redis://default:default@localhost:6379/0"

    # URLs
    RETRIEVAL_SERVICE_GRPC_URL: str = "localhost:15600"
    EXTENSION_SERVICE_URL: str = "http://localhost:15300"
    SCHEDULER_SERVICE_URL: str = "http://localhost:15400"
    FRONTEND_REDIRECT_URL: str = "http://localhost:3000/callback/extension"

    @property
    def POSTGRES_URL_PATH_WITH_SCHEMA(self) -> str:
        """Construct PostgreSQL URL path with schema for SQLAlchemy."""
        return f"{self.POSTGRES_URL_PATH}?options=-csearch_path%3D{self.POSTGRES_SCHEMA}"


@lru_cache()
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

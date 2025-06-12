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
    LLM_DEFAULT_API_KEY: str = "<your-api-key>"
    LLM_DEFAULT_PROVIDER: LlmProvider = LlmProvider.OPENAI
    LLM_DEFAULT_MODEL: str = "gpt-4o-nano"
    LLM_DEFAULT_BASE_URL: str = "https://api.openai.com/v1/chat/completions"
    EMBEDDING_PROVIDER: str = "openai"
    DEFAULT_TEMPERATURE: float = 0.0

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
    RECURSION_LIMIT: int = 25  # Cache settings
    MAX_PERSONAL_TOOLS_PER_USER: int = 500
    MAX_CACHED_USERS: int = 200
    MAX_CACHED_EXTENSION_SERVICES: int = 400
    MAX_CACHED_MCP_USERS: int = 100
    MAX_MCP_CLIENT_INSTANCES_PER_USER: int = 20

    # Upload settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB

    # Sets the number of processors
    MAX_WORKERS: int = 1

    # Celery settings
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Embedding model. See the list of supported models: https://qdrant.github.io/fastembed/examples/Supported_Models/
    DENSE_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    SPARSE_EMBEDDING_MODEL: str = "prithivida/Splade_PP_en_v1"
    FASTEMBED_CACHE_PATH: str = "./fastembed_cache"

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

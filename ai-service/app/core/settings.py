from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LlmProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    # Debug mode
    DEBUG_AGENT: bool = False
    DEBUG_SERVER: bool = False
    DEBUG_SQLALCHEMY: bool = False

    # Logging
    LOGGING_LOG_LEVEL: str = "INFO"

    # LLM
    LLM_DEFAULT_API_KEY: str = "<your-api-key>"
    LLM_DEFAULT_PROVIDER: LlmProvider = LlmProvider.OPENAI
    LLM_DEFAULT_MODEL: str = "gpt-4o-nano"
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
    RECURSION_LIMIT: str = "<recursion-limit>"

    # Cache settings
    MAX_PERSONAL_TOOLS_PER_USER: str = "<max-personal-tools-per-user>"
    MAX_CACHED_USERS: str = "<max-cached-users>"
    MAX_CACHED_TOOL_EXTENSION_SERVICES: str = "<max-cached-tool-extension-services>"

    @property
    def POSTGRES_URL_PATH(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache()
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

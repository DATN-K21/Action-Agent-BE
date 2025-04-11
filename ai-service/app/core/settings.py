from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LlmProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
    )

    # FastAPI settings
    PORT: int = 5001
    HOST: str = "0.0.0.0"
    DBG: bool = False
    HTTPS: bool = False

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_TO_CONSOLE: bool = True

    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"
    POSTGRES_DB: str = "ai-database"

    # SQLAlchemy settings
    SQLALCHEMY_DEBUG: bool = False

    # Tool settings
    TAVILY_API_KEY: str = "<your-api-key>"

    # LLM service settings
    DEFAULT_PROVIDER: LlmProvider = LlmProvider.OPENAI
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_API_KEY: str = "<your-api-key>"

    # Langchain service settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = "<your-api-key>"
    LANGCHAIN_PROJECT: str = "<your-project-id>"

    # Composio service settings
    COMPOSIO_LOGGING_LEVEL: str = "debug"
    COMPOSIO_API_KEY: str = "<your-api-key>"
    COMPOSIO_REDIRECT_URL: str = "https://localhost:5001/callback/extension"

    # Frontend service settings
    FRONTEND_REDIRECT_URL: str = "http://localhost:3000/callback/extension"

    @property
    def POSTGRES_URL_PATH(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache()
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

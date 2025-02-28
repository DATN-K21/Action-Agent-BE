from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    # FastAPI settings
    PORT: int = 5001
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    HTTPS: bool = False

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_TO_CONSOLE: bool = True
    LOG_TO_ELASTICSEARCH: bool = False
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USER: str = "elastic"
    ELASTICSEARCH_PASSWORD: str = "123456"
    ELASTICSEARCH_INDEX: str = "logs"

    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"
    POSTGRES_DB: str = "ai-database"

    # SQLAlchemy settings
    SQLALCHEMY_DEBUG: bool = False

    SCARF_NO_ANALYTICS: bool = True

    # Tool settings
    TAVILY_API_KEY: str = "<your-api-key>"

    # LLM service settings
    OPENAI_API_KEY: str = "<your-api-key>"

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
    FRONTEND_REDIRECT_URL: str = "http://localhost:3000"

    @property
    def POSTGRES_URL_PATH(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


env_settings = Settings()
__all__ = ["env_settings"]

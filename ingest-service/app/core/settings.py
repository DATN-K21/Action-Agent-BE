from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Logging
    DEBUG_MODE: bool = True
    LOGGING_LOG_LEVEL: str = "INFO"

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "documents"

    # OpenAI settings
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_API_KEY: str = "<YOUR-API-KEY>"

    # Azure Blob Storage
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    AZURE_BLOB_CONNECTION_STRING: str = "<your-connection-string>"
    AZURE_BLOB_CONTAINER_NAME: str = "uploadingdev"

    # Celery settings
    RABBITMQ_URL: str = "amqp://root:root@localhost:5672/"
    REDIS_URL: str = "redis://default:default@localhost:6379/0"

    # AI Service API (for updating upload status)
    AI_SERVICE_URL: str = "http://localhost:15200"


@lru_cache
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

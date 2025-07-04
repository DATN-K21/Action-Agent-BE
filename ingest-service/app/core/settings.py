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

    # Debug mode
    DEBUG_MODE: bool = True

    # Logging
    LOGGING_LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str = "<YOUR-API-KEY>"
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"

    # Vectorstore settings
    PGVECTOR_POSTGRES_HOST: str = "localhost"
    PGVECTOR_POSTGRES_PORT: int = 5433
    PGVECTOR_POSTGRES_USER: str = "postgres"
    PGVECTOR_POSTGRES_PASSWORD: str = "123456"
    PGVECTOR_POSTGRES_DB: str = "ai-database"
    PGVECTOR_POSTGRES_SCHEMA: str = "ingestservice"
    PGVECTOR_COLLECTION: str = "documents"

    # Upload settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB

    # Azure Blob Storage
    AZURE_BLOB_CONNECTION_STRING: str = "<your-connection-string>"
    AZURE_BLOB_CONTAINER_NAME: str = "uploadingdev"

    # RabbitMQ settings
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "root"
    RABBITMQ_PASSWORD: str = "root"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_SSL: bool = False

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USER: str = "default"
    REDIS_PASSWORD: str = "default"
    REDIS_SSL: bool = False

    # AI Service API (for updating upload status)
    AI_SERVICE_URL: str = "http://localhost:15200"

    # Sets the number of processors
    MAX_WORKERS: int = 1

    @property
    def PGVECTOR_POSTGRES_URL_PATH(self) -> str:
        """Construct PostgreSQL URL path for SQLAlchemy."""
        return f"{self.PGVECTOR_POSTGRES_USER}:{self.PGVECTOR_POSTGRES_PASSWORD}@{self.PGVECTOR_POSTGRES_HOST}:{self.PGVECTOR_POSTGRES_PORT}/{self.PGVECTOR_POSTGRES_DB}"

    @property
    def PGVECTOR_POSTGRES_URL_PATH_WITH_SCHEMA(self) -> str:
        """Construct PostgreSQL URL path with schema for SQLAlchemy."""
        return f"{self.PGVECTOR_POSTGRES_URL_PATH}?options=-csearch_path%3D{self.PGVECTOR_POSTGRES_SCHEMA}"

    @property
    def RABBITMQ_URL(self) -> str:
        """Construct RabbitMQ URL for Celery broker."""
        schema = "amqps" if self.RABBITMQ_SSL else "amqp"
        return f"{schema}://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL"""
        schema = "rediss" if self.REDIS_SSL else "redis"
        return f"{schema}://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings():
    return Settings()


env_settings = get_settings()
__all__ = ["env_settings"]

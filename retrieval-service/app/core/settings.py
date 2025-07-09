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

    # gRPC server settings
    GRPC_PORT: int = 15600

    # Logging
    LOGGING_LOG_LEVEL: str = "INFO"

    # OpenAI for embeddings
    OPENAI_API_KEY: str = "<YOUR-API-KEY>"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"

    # PGVector settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "documents"


@lru_cache
def get_settings() -> Settings:
    return Settings()


env_settings = get_settings()

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Debug mode
    DEBUG_SQLALCHEMY: bool = False

    # Database settings
    POSTGRES_URL_PATH: str = "postgres:123456@localhost:5432/ai-database"
    POSTGRES_SCHEMA: str = "schedulerservice"

    # AI Service settings
    AI_SERVICE_URL: str = "http://localhost:8001"

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Scheduler settings
    MAX_CONCURRENT_JOBS: int = 10
    SCHEDULER_TIMEZONE: str = "Asia/Ho_Chi_Minh"

    # Job execution settings
    JOB_TIMEOUT: int = 300
    MAX_RETRIES: int = 3

    # API settings
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")

    @property
    def POSTGRES_URL_PATH_WITH_SCHEMA(self) -> str:
        """Construct PostgreSQL URL path with schema for SQLAlchemy."""
        return f"{self.POSTGRES_URL_PATH}?options=-csearch_path%3D{self.POSTGRES_SCHEMA}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


env_settings = get_settings()

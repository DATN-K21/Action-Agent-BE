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
    POSTGRES_URL_PATH: str = Field(
        default="postgres:123456@localhost:5432/ai-database",
        description="PostgreSQL database connection URL path (without protocol)"
    )
    POSTGRES_SCHEMA: str = Field(
        default="schedulerservice",
        description="PostgreSQL schema name"
    )

    # AI Service settings
    AI_SERVICE_URL: str = Field(
        default="http://localhost:8001", description="AI Service base URL"
    )

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG_SERVER: bool = Field(default=False, description="Enable debug mode")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Scheduler settings
    SCHEDULER_TIMEZONE: str = Field(default="UTC", description="Scheduler timezone")
    MAX_CONCURRENT_JOBS: int = Field(default=10, description="Maximum concurrent jobs")

    # Job execution settings
    JOB_TIMEOUT: int = Field(default=300, description="Job timeout in seconds")
    MAX_RETRIES: int = Field(default=3, description="Maximum job retries")

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

from typing import Optional

from pydantic import Field

from app.schemas.base import BaseResponse


class HealthResponse(BaseResponse):
    """Schema for health check response."""
    status: str = Field(..., description="Overall health status")
    scheduler_running: bool = Field(..., description="Whether scheduler is running")
    database_status: str = Field(..., description="Database connection status")
    message: Optional[str] = Field(None, description="Additional health information")


class DatabaseHealthResponse(BaseResponse):
    """Schema for database health check response."""
    status: str = Field(..., description="Database connection status")
    message: Optional[str] = Field(None, description="Database health message")
    connection_count: Optional[int] = Field(None, description="Number of active connections") 
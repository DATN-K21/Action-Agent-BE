from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseEntity
from app.core.settings import env_settings


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type."""
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class ScheduledJob(BaseEntity):
    """Database model for scheduled jobs."""
    
    __tablename__ = "scheduled_jobs"
    __table_args__ = {"schema": env_settings.POSTGRES_SCHEMA}

    # Basic job information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Job type and scheduling
    job_type: Mapped[JobType] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Execution details
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    team_id: Mapped[str] = mapped_column(String(255), nullable=False)
    assistant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_service_endpoint: Mapped[str] = mapped_column(String(255), default="/api/v1/team/stream", nullable=False)
    
    # Job configuration
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(default=300, nullable=False)
    
    # Job metadata
    job_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and execution info
    status: Mapped[JobStatus] = mapped_column(String(50), default=JobStatus.PENDING, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Execution tracking
    total_runs: Mapped[int] = mapped_column(default=0, nullable=False)
    successful_runs: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_runs: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Active/inactive status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # User who created the job
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"<ScheduledJob {self.name} ({self.status})>"


class JobExecution(BaseEntity):
    """Database model for job execution logs."""
    
    __tablename__ = "job_executions"
    __table_args__ = {"schema": env_settings.POSTGRES_SCHEMA}

    # Job reference
    job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Execution details
    status: Mapped[JobStatus] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Execution data
    prompt_sent: Mapped[str] = mapped_column(Text, nullable=False)
    response_received: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Retry information
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    is_retry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Execution metadata
    execution_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<JobExecution {self.job_id} ({self.status})>"

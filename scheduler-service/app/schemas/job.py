from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus, JobType
from app.schemas.base import BaseRequest, BaseResponse


class JobBase(BaseModel):
    """Base job schema."""
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    prompt: str = Field(..., description="Prompt to send to AI service")
    team_id: str = Field(..., description="Team ID for the job")
    assistant_id: str = Field(..., description="Assistant ID for the job")
    job_config: Optional[Dict] = Field(None, description="Additional job configuration")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout_seconds: int = Field(default=300, description="Job timeout in seconds")


class JobCreate(JobBase, BaseRequest):
    """Schema for creating a new job."""
    job_type: JobType = Field(..., description="Job type (one_time or recurring)")
    cron_expression: Optional[str] = Field(None, description="Cron expression for recurring jobs")
    is_active: bool = Field(default=True, description="Whether the job is active")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Daily Report",
                "description": "Send daily report to team",
                "job_type": "recurring",
                "cron_expression": "0 9 * * *",
                "prompt": "Generate daily report for team activities",
                "team_id": "team-123",
                "assistant_id": "assistant-456",
                "max_retries": 3,
                "timeout_seconds": 300,
                "is_active": True,
                "job_config": {"format": "markdown", "include_metrics": True},
            }
        }
    )


class JobUpdate(BaseRequest):
    """Schema for updating a job."""
    name: Optional[str] = Field(None, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    prompt: Optional[str] = Field(None, description="Prompt to send to AI service")
    team_id: Optional[str] = Field(None, description="Team ID")
    assistant_id: Optional[str] = Field(None, description="Assistant ID")
    job_config: Optional[Dict] = Field(None, description="Job configuration")
    max_retries: Optional[int] = Field(None, description="Maximum retries")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")
    is_active: Optional[bool] = Field(None, description="Whether job is active")


class JobResponse(JobBase, BaseResponse):
    """Schema for job response."""
    id: str = Field(..., description="Job ID")
    job_type: JobType = Field(..., description="Job type")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    status: JobStatus = Field(..., description="Job status")
    is_active: bool = Field(..., description="Whether job is active")
    user_id: str = Field(..., description="User who created the job")
    user_role: Optional[str] = Field(None, description="Role of the user who created the job")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_run_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    next_run_at: Optional[datetime] = Field(None, description="Next execution timestamp")
    total_runs: int = Field(..., description="Total number of runs")
    successful_runs: int = Field(..., description="Number of successful runs")
    failed_runs: int = Field(..., description="Number of failed runs")
    
    model_config = ConfigDict(from_attributes=True)


class JobsResponse(BaseResponse):
    jobs: list[JobResponse] = Field(..., description="List of jobs")


class JobExecutionResponse(BaseResponse):
    """Schema for job execution response."""
    id: str = Field(..., description="Execution ID")
    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    prompt_sent: str = Field(..., description="Prompt that was sent")
    response_received: Optional[str] = Field(None, description="Response received")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., description="Retry count")
    is_retry: bool = Field(..., description="Whether this is a retry")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class JobExecutionsResponse(BaseResponse):
    executions: list[JobExecutionResponse] = Field(
        ..., description="List of job executions"
    )


class JobStats(BaseResponse):
    """Schema for job statistics."""
    total_jobs: int = Field(..., description="Total number of jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    paused_jobs: int = Field(..., description="Number of paused jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")


class CronValidationRequest(BaseRequest):
    """Schema for cron expression validation."""
    cron_expression: str = Field(..., description="Cron expression to validate")
    timezone: str = Field(default="UTC", description="Timezone for validation")


class CronValidationResponse(BaseResponse):
    """Schema for cron validation response."""
    is_valid: bool = Field(..., description="Whether cron expression is valid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
    next_run_times: Optional[list[datetime]] = Field(None, description="Next 5 run times")


class JobRunRequest(BaseRequest):
    """Schema for manual job execution request."""
    reason: Optional[str] = Field(None, description="Reason for manual execution")


class JobRunResponse(BaseResponse):
    """Schema for job run response."""
    success: bool = Field(..., description="Whether job was triggered successfully")
    message: str = Field(..., description="Response message")
    execution_id: Optional[str] = Field(None, description="Execution ID if successful")

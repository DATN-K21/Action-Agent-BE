from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path, Header
from croniter import croniter

from app.core import logging
from app.core.scheduler import scheduler_manager
from app.models.job import JobStatus, JobType
from app.schemas.job import (
    JobCreate, JobUpdate, JobResponse, JobExecutionResponse,
    JobStats, CronValidationRequest, CronValidationResponse,
    JobRunRequest, JobRunResponse
)
from app.services.job_service import job_service

logger = logging.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=JobResponse, summary="Create Job")
async def create_job(
    job_data: JobCreate,
    x_user_id=Header(None),
    x_user_role=Header(None)
):
    """
    Create a new scheduled job.
    
    - **name**: Job name
    - **description**: Optional job description
    - **job_type**: Type of job (one_time or recurring)
    - **cron_expression**: Cron expression for recurring jobs
    - **prompt**: Prompt to send to AI service
    - **team_id**: Team ID for the job
    - **assistant_id**: Assistant ID for the job
    - **max_retries**: Maximum number of retries (default: 3)
    - **timeout_seconds**: Job timeout in seconds (default: 300)
    - **timezone**: Job timezone (default: UTC)
    - **is_active**: Whether the job is active (default: True)
    - **job_config**: Additional job configuration
    """
    try:
        if not x_user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required (x_user_id header)"
            )
        
        # Validate cron expression for recurring jobs
        if job_data.job_type == JobType.RECURRING:
            if not job_data.cron_expression:
                raise HTTPException(
                    status_code=400,
                    detail="Cron expression is required for recurring jobs"
                )
            
            if not scheduler_manager.is_valid_cron(job_data.cron_expression):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid cron expression"
                )
        
        job = await job_service.create_job(job_data, x_user_id, x_user_role)
        logger.info(f"Job created: {job.id}")
        return job
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[JobResponse], summary="List Jobs")
async def list_jobs(
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of jobs to return"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    assistant_id: Optional[str] = Query(None, description="Filter by assistant ID"),
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    x_user_id=Header(None),
    x_user_role=Header(None)
):
    """
    Get list of scheduled jobs with optional filtering.
    
    - **skip**: Number of jobs to skip for pagination
    - **limit**: Maximum number of jobs to return
    - **status**: Filter by job status
    - **job_type**: Filter by job type
    - **assistant_id**: Filter by assistant ID (optional)
    - **team_id**: Filter by team ID (optional)
    
    Users can only see their own jobs unless they are admin or super admin.
    If assistant_id or team_id are provided, jobs will be filtered by these values.
    If they are empty, all jobs for the user will be returned.
    """
    try:
        if not x_user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required (x_user_id header)"
            )
        
        # Determine user filter based on role
        user_filter = None if x_user_role in ["admin", "super admin"] else x_user_id
        
        jobs = await job_service.get_jobs(
            skip=skip,
            limit=limit,
            status=status,
            job_type=job_type,
            created_by=user_filter,
            assistant_id=assistant_id,
            team_id=team_id
        )
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobResponse, summary="Get Job")
async def get_job(
    job_id: str = Path(..., description="Job ID"),
    x_user_id=Header(None),
    x_user_role=Header(None)
):
    """
    Get details of a specific job.
    
    - **job_id**: Unique job identifier
    
    Users can only access their own jobs unless they are admin or super admin.
    """
    try:
        if not x_user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required (x_user_id header)"
            )
        
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check authorization
        if x_user_role not in ["admin", "super admin"] and job.user_id != x_user_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=JobResponse, summary="Update Job")
async def update_job(
    job_update: JobUpdate,
    job_id: str = Path(..., description="Job ID")
):
    """
    Update an existing job.
    
    - **job_id**: Unique job identifier
    - **job_update**: Updated job data
    """
    try:
        # Validate cron expression if provided
        if job_update.cron_expression:
            if not scheduler_manager.is_valid_cron(job_update.cron_expression):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid cron expression"
                )
        
        job = await job_service.update_job(job_id, job_update)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Job updated: {job_id}")
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", summary="Delete Job")
async def delete_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Delete a job (soft delete).
    
    - **job_id**: Unique job identifier
    """
    try:
        success = await job_service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Job deleted: {job_id}")
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/run", response_model=JobRunResponse, summary="Run Job Now")
async def run_job_now(
    job_id: str = Path(..., description="Job ID"),
    run_request: Optional[JobRunRequest] = None
):
    """
    Manually trigger a job execution.
    
    - **job_id**: Unique job identifier
    - **run_request**: Optional reason for manual execution
    """
    try:
        success = await job_service.run_job_now(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or could not be executed")
        
        logger.info(f"Job triggered manually: {job_id}")
        return JobRunResponse(
            success=True,
            message="Job execution triggered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/pause", summary="Pause Job")
async def pause_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Pause a running job.
    
    - **job_id**: Unique job identifier
    """
    try:
        success = await job_service.pause_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or could not be paused")
        
        logger.info(f"Job paused: {job_id}")
        return {"message": "Job paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/resume", summary="Resume Job")
async def resume_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Resume a paused job.
    
    - **job_id**: Unique job identifier
    """
    try:
        success = await job_service.resume_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or could not be resumed")
        
        logger.info(f"Job resumed: {job_id}")
        return {"message": "Job resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/executions", response_model=List[JobExecutionResponse], summary="Get Job Executions")
async def get_job_executions(
    job_id: str = Path(..., description="Job ID"),
    skip: int = Query(0, ge=0, description="Number of executions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of executions to return")
):
    """
    Get execution history for a job.
    
    - **job_id**: Unique job identifier
    - **skip**: Number of executions to skip for pagination
    - **limit**: Maximum number of executions to return
    """
    try:
        executions = await job_service.get_job_executions(job_id, skip, limit)
        return executions
        
    except Exception as e:
        logger.error(f"Failed to get executions for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-cron", response_model=CronValidationResponse, summary="Validate Cron Expression")
async def validate_cron(
    request: CronValidationRequest
):
    """
    Validate a cron expression and get next run times.
    
    - **cron_expression**: Cron expression to validate
    - **timezone**: Timezone for validation (default: UTC)
    """
    try:
        is_valid = scheduler_manager.is_valid_cron(request.cron_expression)
        
        if not is_valid:
            return CronValidationResponse(
                is_valid=False,
                error_message="Invalid cron expression format"
            )
        
        # Get next 5 run times
        next_runs = []
        try:
            cron = croniter(request.cron_expression, datetime.now())
            for _ in range(5):
                next_runs.append(cron.get_next(datetime))
        except Exception:
            pass
        
        return CronValidationResponse(
            is_valid=True,
            next_run_times=next_runs
        )
        
    except Exception as e:
        logger.error(f"Failed to validate cron expression: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=JobStats, summary="Get Job Statistics")
async def get_job_stats():
    """
    Get overview statistics for all jobs.
    """
    try:
        # This would be implemented with proper database queries
        # For now, returning mock data
        return JobStats(
            total_jobs=0,
            active_jobs=0,
            paused_jobs=0,
            failed_jobs=0,
            total_executions=0,
            successful_executions=0,
            failed_executions=0
        )
        
    except Exception as e:
        logger.error(f"Failed to get job stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

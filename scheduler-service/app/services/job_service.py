from typing import List, Optional

from sqlalchemy import and_, select, update

from app.core import logging
from app.core.database import AsyncSessionLocal
from app.core.scheduler import scheduler_manager
from app.models.job import JobExecution, JobStatus, JobType, ScheduledJob
from app.schemas.job import JobCreate, JobExecutionResponse, JobResponse, JobUpdate

logger = logging.get_logger(__name__)


class JobService:
    """Service layer for job operations."""

    async def create_job(
        self,
        job_data: JobCreate,
        user_id: str,
        user_role: str,
        user_timezone: str,
    ) -> JobResponse:
        """Create a new scheduled job."""
        try:
            async with AsyncSessionLocal() as session:
                # Create job record
                job = ScheduledJob(
                    name=job_data.name,
                    description=job_data.description,
                    job_type=job_data.job_type,
                    cron_expression=job_data.cron_expression,
                    prompt=job_data.prompt,
                    team_id=job_data.team_id,
                    assistant_id=job_data.assistant_id,
                    max_retries=job_data.max_retries,
                    timeout_seconds=job_data.timeout_seconds,
                    job_config=job_data.job_config,
                    is_active=job_data.is_active,
                    next_run_at=scheduler_manager.get_next_run_time(
                        job_data.cron_expression
                    )
                    if job_data.cron_expression
                    else None,
                    user_id=user_id,
                    user_role=user_role,
                    timezone=user_timezone,
                )
                
                session.add(job)
                await session.commit()
                await session.refresh(job)
                
                # Add job to scheduler if it's a recurring job and active
                if job.job_type == JobType.RECURRING and job.is_active and job.cron_expression:
                    job_execution_data = {
                        "prompt": job.prompt,
                        "user_id": job.user_id,
                        "user_role": job.user_role,
                        "user_timezone": job.timezone,
                        "team_id": job.team_id,
                        "assistant_id": job.assistant_id,
                        "job_config": job.job_config or {},
                    }
                    
                    success = await scheduler_manager.add_job(
                        job_id=job.id,
                        cron_expression=job.cron_expression,
                        job_data=job_execution_data,
                        timezone=job.timezone
                    )
                    
                    if not success:
                        logger.error(f"Failed to add job to scheduler: {job.id}")
                        # Update job status to failed
                        await session.execute(
                            update(ScheduledJob)
                            .where(ScheduledJob.id == job.id)
                            .values(status=JobStatus.FAILED)
                        )
                        await session.commit()
                
                logger.info(f"Successfully created job: {job.id}")
                return JobResponse.from_orm(job)
        
        except Exception as e:
            logger.exception(f"Failed to create job: {str(e)}")
            raise
    
    async def get_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> List[JobResponse]:
        """Get list of jobs with optional filtering."""
        try:
            async with AsyncSessionLocal() as session:
                query = select(ScheduledJob).where(ScheduledJob.is_deleted.is_(False))
                
                # Apply filters
                if status:
                    query = query.where(ScheduledJob.status == status)
                if job_type:
                    query = query.where(ScheduledJob.job_type == job_type)
                if user_id:
                    query = query.where(ScheduledJob.user_id == user_id)
                if assistant_id:
                    query = query.where(ScheduledJob.assistant_id == assistant_id)
                if team_id:
                    query = query.where(ScheduledJob.team_id == team_id)
                
                # Apply pagination
                query = query.offset(skip).limit(limit)
                
                result = await session.execute(query)
                jobs = result.scalars().all()
                
                logger.info(f"Retrieved {len(jobs)} jobs with filters: status={status}, job_type={job_type}, user_id={user_id}")
                return [JobResponse.from_orm(job) for job in jobs]
        
        except Exception as e:
            logger.exception(f"Failed to retrieve jobs: {str(e)}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get a specific job by ID."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ScheduledJob).where(
                        and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False))
                    )
                )
                job = result.scalar_one_or_none()
                
                if job:
                    logger.info(f"Retrieved job: {job_id}")
                    return JobResponse.from_orm(job)
                else:
                    logger.warning(f"Job not found: {job_id}")
                    return None
        
        except Exception as e:
            logger.exception(f"Failed to retrieve job {job_id}: {str(e)}")
            raise
    
    async def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[JobResponse]:
        """Update a job."""
        try:
            async with AsyncSessionLocal() as session:
                # Get existing job
                result = await session.execute(
                    select(ScheduledJob).where(
                        and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False))
                    )
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.warning(f"Job not found for update: {job_id}")
                    return None
                
                # Update job fields
                update_data = job_update.model_dump(exclude_unset=True)
                
                # Handle scheduler updates
                old_cron = job.cron_expression
                old_active = job.is_active
                
                # Update job record
                await session.execute(
                    update(ScheduledJob)
                    .where(ScheduledJob.id == job_id)
                    .values(**update_data)
                )
                await session.commit()
                
                # Refresh job to get updated values
                await session.refresh(job)
                
                # Update scheduler if needed
                if job.job_type == JobType.RECURRING:
                    # Remove old job from scheduler
                    if old_cron and old_active:
                        await scheduler_manager.remove_job(job_id)
                    
                    # Add updated job to scheduler
                    if job.cron_expression and job.is_active:
                        job_execution_data = {
                            "prompt": job.prompt,
                            "user_id": job.user_id,
                            "user_role": job.user_role,
                            "user_timezone": job.timezone,
                            "assistant_id": job.assistant_id,
                            "team_id": job.team_id,
                            "job_config": job.job_config or {},
                        }
                        
                        await scheduler_manager.add_job(
                            job_id=job.id,
                            cron_expression=job.cron_expression,
                            job_data=job_execution_data,
                            timezone=job.timezone
                        )
                
                logger.info(f"Successfully updated job: {job_id}")
                return JobResponse.from_orm(job)
        
        except Exception as e:
            logger.exception(f"Failed to update job {job_id}: {str(e)}")
            raise
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job (soft delete)."""
        try:
            async with AsyncSessionLocal() as session:
                # Check if job exists
                result = await session.execute(
                    select(ScheduledJob).where(
                        and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False))
                    )
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.warning(f"Job not found for deletion: {job_id}")
                    return False
                
                # Remove from scheduler
                await scheduler_manager.remove_job(job_id)
                
                # Soft delete
                await session.execute(
                    update(ScheduledJob)
                    .where(ScheduledJob.id == job_id)
                    .values(is_deleted=True, is_active=False)
                )
                await session.commit()
                
                logger.info(f"Successfully deleted job: {job_id}")
                return True
        
        except Exception as e:
            logger.exception(f"Failed to delete job {job_id}: {str(e)}")
            raise
    
    async def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job execution."""
        try:
            async with AsyncSessionLocal() as session:
                # Get job details
                result = await session.execute(
                    select(ScheduledJob).where(
                        and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False))
                    )
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.warning(f"Job not found for manual execution: {job_id}")
                    return False
                
                # Prepare job execution data
                job_execution_data = {
                    "prompt": job.prompt,
                    "user_id": job.user_id,
                    "user_role": job.user_role,
                    "user_timezone": job.timezone,
                    "assistant_id": job.assistant_id,
                    "team_id": job.team_id,
                    "job_config": job.job_config or {},
                }
                
                # Run job
                result = await scheduler_manager.run_job_now(job_id, job_execution_data)
                
                if result:
                    logger.info(f"Successfully triggered manual execution for job: {job_id}")
                else:
                    logger.warning(f"Failed to trigger manual execution for job: {job_id}")
                
                return result
        
        except Exception as e:
            logger.exception(f"Failed to run job {job_id}: {str(e)}")
            raise
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            async with AsyncSessionLocal() as session:
                # Update job status
                result = await session.execute(
                    update(ScheduledJob)
                    .where(and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False)))
                    .values(status=JobStatus.PAUSED)
                )
                await session.commit()
                
                if result.rowcount == 0:
                    logger.warning(f"Job not found for pause: {job_id}")
                    return False
                
                # Pause in scheduler
                scheduler_result = await scheduler_manager.pause_job(job_id)
                
                if scheduler_result:
                    logger.info(f"Successfully paused job: {job_id}")
                else:
                    logger.warning(f"Failed to pause job in scheduler: {job_id}")
                
                return scheduler_result
        
        except Exception as e:
            logger.exception(f"Failed to pause job {job_id}: {str(e)}")
            raise
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            async with AsyncSessionLocal() as session:
                # Update job status
                result = await session.execute(
                    update(ScheduledJob)
                    .where(and_(ScheduledJob.id == job_id, ScheduledJob.is_deleted.is_(False)))
                    .values(status=JobStatus.PENDING)
                )
                await session.commit()
                
                if result.rowcount == 0:
                    logger.warning(f"Job not found for resume: {job_id}")
                    return False
                
                # Resume in scheduler
                scheduler_result = await scheduler_manager.resume_job(job_id)
                
                if scheduler_result:
                    logger.info(f"Successfully resumed job: {job_id}")
                else:
                    logger.warning(f"Failed to resume job in scheduler: {job_id}")
                
                return scheduler_result
        
        except Exception as e:
            logger.exception(f"Failed to resume job {job_id}: {str(e)}")
            raise
    
    async def get_job_executions(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobExecutionResponse]:
        """Get execution history for a job."""
        try:
            async with AsyncSessionLocal() as session:
                query = (
                    select(JobExecution)
                    .where(JobExecution.job_id == job_id)
                    .order_by(JobExecution.created_at.desc())
                    .offset(skip)
                    .limit(limit)
                )
                
                result = await session.execute(query)
                executions = result.scalars().all()
                
                logger.info(f"Retrieved {len(executions)} executions for job: {job_id}")
                return [JobExecutionResponse.from_orm(execution) for execution in executions]
        
        except Exception as e:
            logger.exception(f"Failed to retrieve executions for job {job_id}: {str(e)}")
            raise


# Global service instance
job_service = JobService()

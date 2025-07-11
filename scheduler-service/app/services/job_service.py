from typing import List, Optional

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.database import async_session_factory
from app.core.scheduler import scheduler_manager
from app.models.job import ScheduledJob, JobExecution, JobStatus, JobType
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobExecutionResponse

logger = logging.get_logger(__name__)


class JobService:
    """Service layer for job operations."""
    
    async def create_job(self, job_data: JobCreate, created_by: str) -> JobResponse:
        """Create a new scheduled job."""
        async with async_session_factory() as session:
            # Create job record
            job = ScheduledJob(
                name=job_data.name,
                description=job_data.description,
                job_type=job_data.job_type,
                cron_expression=job_data.cron_expression,
                timezone=job_data.timezone,
                prompt=job_data.prompt,
                team_id=job_data.team_id,
                ai_service_endpoint=job_data.ai_service_endpoint,
                max_retries=job_data.max_retries,
                timeout_seconds=job_data.timeout_seconds,
                job_config=job_data.job_config,
                created_by=created_by,
                is_active=job_data.is_active,
                next_run_at=scheduler_manager.get_next_run_time(job_data.cron_expression) if job_data.cron_expression else None
            )
            
            session.add(job)
            await session.commit()
            await session.refresh(job)
            
            # Add job to scheduler if it's a recurring job and active
            if job.job_type == JobType.RECURRING and job.is_active and job.cron_expression:
                job_execution_data = {
                    'prompt': job.prompt,
                    'team_id': job.team_id,
                    'ai_service_endpoint': job.ai_service_endpoint,
                    'job_config': job.job_config or {}
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
            
            return JobResponse.from_orm(job)
    
    async def get_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        created_by: Optional[str] = None
    ) -> List[JobResponse]:
        """Get list of jobs with optional filtering."""
        async with async_session_factory() as session:
            query = select(ScheduledJob).where(ScheduledJob.is_deleted == False)
            
            # Apply filters
            if status:
                query = query.where(ScheduledJob.status == status)
            if job_type:
                query = query.where(ScheduledJob.job_type == job_type)
            if created_by:
                query = query.where(ScheduledJob.created_by == created_by)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            jobs = result.scalars().all()
            
            return [JobResponse.from_orm(job) for job in jobs]
    
    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get a specific job by ID."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(ScheduledJob)
                .where(
                    and_(
                        ScheduledJob.id == job_id,
                        ScheduledJob.is_deleted == False
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if job:
                return JobResponse.from_orm(job)
            return None
    
    async def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[JobResponse]:
        """Update a job."""
        async with async_session_factory() as session:
            # Get existing job
            result = await session.execute(
                select(ScheduledJob)
                .where(
                    and_(
                        ScheduledJob.id == job_id,
                        ScheduledJob.is_deleted == False
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
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
                        'prompt': job.prompt,
                        'team_id': job.team_id,
                        'ai_service_endpoint': job.ai_service_endpoint,
                        'job_config': job.job_config or {}
                    }
                    
                    await scheduler_manager.add_job(
                        job_id=job.id,
                        cron_expression=job.cron_expression,
                        job_data=job_execution_data,
                        timezone=job.timezone
                    )
            
            return JobResponse.from_orm(job)
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job (soft delete)."""
        async with async_session_factory() as session:
            # Check if job exists
            result = await session.execute(
                select(ScheduledJob)
                .where(
                    and_(
                        ScheduledJob.id == job_id,
                        ScheduledJob.is_deleted == False
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
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
            
            return True
    
    async def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job execution."""
        async with async_session_factory() as session:
            # Get job details
            result = await session.execute(
                select(ScheduledJob)
                .where(
                    and_(
                        ScheduledJob.id == job_id,
                        ScheduledJob.is_deleted == False
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False
            
            # Prepare job execution data
            job_execution_data = {
                'prompt': job.prompt,
                'team_id': job.team_id,
                'ai_service_endpoint': job.ai_service_endpoint,
                'job_config': job.job_config or {}
            }
            
            # Run job
            return await scheduler_manager.run_job_now(job_id, job_execution_data)
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        async with async_session_factory() as session:
            # Update job status
            await session.execute(
                update(ScheduledJob)
                .where(ScheduledJob.id == job_id)
                .values(status=JobStatus.PAUSED)
            )
            await session.commit()
            
            # Pause in scheduler
            return await scheduler_manager.pause_job(job_id)
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        async with async_session_factory() as session:
            # Update job status
            await session.execute(
                update(ScheduledJob)
                .where(ScheduledJob.id == job_id)
                .values(status=JobStatus.PENDING)
            )
            await session.commit()
            
            # Resume in scheduler
            return await scheduler_manager.resume_job(job_id)
    
    async def get_job_executions(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobExecutionResponse]:
        """Get execution history for a job."""
        async with async_session_factory() as session:
            query = (
                select(JobExecution)
                .where(JobExecution.job_id == job_id)
                .order_by(JobExecution.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            executions = result.scalars().all()
            
            return [JobExecutionResponse.from_orm(execution) for execution in executions]


# Global service instance
job_service = JobService()

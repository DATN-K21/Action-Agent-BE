import asyncio
from datetime import datetime
from typing import Dict, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.database import AsyncSessionLocal
from app.core.settings import env_settings
from app.models.job import ScheduledJob, JobExecution, JobStatus

logger = logging.get_logger(__name__)


class JobExecutor:
    """Handles job execution logic."""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=env_settings.JOB_TIMEOUT)
    
    async def execute_job(self, job_id: str, job_data: Dict) -> None:
        """Execute a scheduled job."""
        execution_id = None
        start_time = datetime.utcnow()
        
        try:
            # Create execution record
            async with AsyncSessionLocal() as session:
                execution = JobExecution(
                    job_id=job_id,
                    status=JobStatus.RUNNING,
                    started_at=start_time,
                    prompt_sent=job_data.get('prompt', ''),
                    execution_metadata=job_data
                )
                session.add(execution)
                await session.commit()
                execution_id = execution.id
                
                # Update job status
                await session.execute(
                    update(ScheduledJob)
                    .where(ScheduledJob.id == job_id)
                    .values(
                        status=JobStatus.RUNNING,
                        last_run_at=start_time,
                        total_runs=ScheduledJob.total_runs + 1
                    )
                )
                await session.commit()
            
            logger.info(f"Starting job execution: {job_id}")
            
            # Execute the job
            response = await self._send_prompt_to_ai_service(job_data)
            
            # Mark execution as successful
            await self._update_execution_success(
                execution_id,
                response,
                start_time
            )
            
            # Update job success stats
            await self._update_job_success(job_id)
            
            logger.info(f"Job execution completed successfully: {job_id}")
            
        except Exception as e:
            logger.error(f"Job execution failed: {job_id} - {str(e)}")
            
            # Mark execution as failed
            if execution_id:
                await self._update_execution_failure(
                    execution_id,
                    str(e),
                    start_time
                )
            
            # Update job failure stats
            await self._update_job_failure(job_id)
            
            # Check if retry is needed
            await self._handle_retry(job_id, job_data, str(e))
    
    async def _send_prompt_to_ai_service(self, job_data: Dict) -> str:
        """Send prompt to AI service."""
        try:
            url = f"{env_settings.AI_SERVICE_URL}{job_data.get('ai_service_endpoint', '/api/v1/team/stream')}"
            
            payload = {
                "prompt": job_data.get('prompt'),
                "team_id": job_data.get('team_id'),
                **job_data.get('job_config', {})
            }
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            return response.text
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")
    
    async def _update_execution_success(
        self,
        execution_id: str,
        response: str,
        start_time: datetime
    ) -> None:
        """Update execution record with success."""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(JobExecution)
                .where(JobExecution.id == execution_id)
                .values(
                    status=JobStatus.SUCCESS,
                    completed_at=end_time,
                    duration_seconds=duration,
                    response_received=response
                )
            )
            await session.commit()
    
    async def _update_execution_failure(
        self,
        execution_id: str,
        error_message: str,
        start_time: datetime
    ) -> None:
        """Update execution record with failure."""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(JobExecution)
                .where(JobExecution.id == execution_id)
                .values(
                    status=JobStatus.FAILED,
                    completed_at=end_time,
                    duration_seconds=duration,
                    error_message=error_message
                )
            )
            await session.commit()
    
    async def _update_job_success(self, job_id: str) -> None:
        """Update job success statistics."""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(ScheduledJob)
                .where(ScheduledJob.id == job_id)
                .values(
                    status=JobStatus.SUCCESS,
                    successful_runs=ScheduledJob.successful_runs + 1
                )
            )
            await session.commit()
    
    async def _update_job_failure(self, job_id: str) -> None:
        """Update job failure statistics."""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(ScheduledJob)
                .where(ScheduledJob.id == job_id)
                .values(
                    status=JobStatus.FAILED,
                    failed_runs=ScheduledJob.failed_runs + 1
                )
            )
            await session.commit()
    
    async def _handle_retry(self, job_id: str, job_data: Dict, error_message: str) -> None:
        """Handle job retry logic."""
        async with AsyncSessionLocal() as session:
            # Get job details
            result = await session.execute(
                select(ScheduledJob).where(ScheduledJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job not found for retry: {job_id}")
                return
            
            # Check if we should retry
            if job.failed_runs < job.max_retries:
                logger.info(f"Scheduling retry for job {job_id} (attempt {job.failed_runs + 1})")
                
                # Schedule retry with exponential backoff
                retry_delay = 2 ** job.failed_runs  # 2, 4, 8, 16 seconds
                await asyncio.sleep(retry_delay)
                
                # Create retry execution
                retry_execution = JobExecution(
                    job_id=job_id,
                    status=JobStatus.PENDING,
                    started_at=datetime.utcnow(),
                    prompt_sent=job_data.get('prompt', ''),
                    is_retry=True,
                    retry_count=job.failed_runs + 1,
                    execution_metadata=job_data
                )
                session.add(retry_execution)
                await session.commit()
                
                # Execute retry
                await self.execute_job(job_id, job_data)
            else:
                logger.error(f"Max retries exceeded for job {job_id}")
                
                # Mark job as permanently failed
                await session.execute(
                    update(ScheduledJob)
                    .where(ScheduledJob.id == job_id)
                    .values(status=JobStatus.FAILED)
                )
                await session.commit()
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

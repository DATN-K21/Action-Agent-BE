import asyncio
from datetime import datetime
from typing import Dict

import httpx
from sqlalchemy import select, update

from app.core import logging
from app.core.database import AsyncSessionLocal
from app.core.settings import env_settings
from app.models.job import JobExecution, JobStatus, ScheduledJob

logger = logging.get_logger(__name__)


class JobExecutor:
    """Handles job execution logic."""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=env_settings.JOB_TIMEOUT)
        self._ai_service_available = None

    async def _check_ai_service_health(self) -> bool:
        """Check if AI service is accessible."""
        try:
            health_url = f"{env_settings.AI_SERVICE_URL}/ping"
            response = await self.http_client.get(health_url, timeout=5.0)
            response.raise_for_status()
            self._ai_service_available = True
            logger.info(f"AI service is accessible at {env_settings.AI_SERVICE_URL}")
            return True
        except Exception as e:
            self._ai_service_available = False
            logger.error(
                f"AI service health check failed at {env_settings.AI_SERVICE_URL}: {str(e)}"
            )
            return False
    
    async def execute_job(self, job_id: str, job_data: Dict) -> None:
        """Execute a scheduled job."""
        execution_id = None
        start_time = datetime.utcnow()
        
        try:
            # Check AI service availability first
            if not await self._check_ai_service_health():
                raise Exception(
                    f"AI service is not available at {env_settings.AI_SERVICE_URL}"
                )

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
                await session.refresh(execution)
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
            thread_id = await self._create_thread_id(job_id, job_data)
            response = await self._send_prompt_to_ai_service(thread_id, job_data)
            
            # Mark execution as successful
            await self._update_execution_success(
                execution_id, thread_id, response, start_time
            )
            
            # Update job success stats
            await self._update_job_success(job_id)
            
            logger.info(f"Job execution completed successfully: {job_id}")
            
        except Exception as e:
            logger.exception(f"Job execution failed: {job_id} - {str(e)}")
            
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

    async def _create_thread_id(self, job_id: str, job_data: Dict) -> str:
        """Create a new thread ID from AI service."""
        try:
            url = f"{env_settings.AI_SERVICE_URL}/api/v1/thread/create"

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-User-Id": job_data.get("user_id", ""),
                "X-User-Role": job_data.get("user_role", ""),
                "X-User-Timezone": job_data.get("user_timezone", ""),
            }

            payload = {
                "title": f"Run the job: {job_id}",
                "assistant_id": job_data.get("assistant_id", ""),
            }

            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            thread_data = response.json()
            thread_id = thread_data.get("data", {}).get("id", "")
            logger.info(f"Successfully created thread: {thread_id}")
            return thread_id

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to create thread - HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.ConnectError:
            error_msg = f"Failed to create thread - Connection error: Unable to connect to AI service at {env_settings.AI_SERVICE_URL}. Please check if the service is running and accessible."
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException:
            error_msg = f"Failed to create thread - Timeout error: AI service at {env_settings.AI_SERVICE_URL} did not respond within {env_settings.JOB_TIMEOUT} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Failed to create thread - Request error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to create thread - Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def _send_prompt_to_ai_service(self, thread_id: str, job_data: Dict) -> str:
        """Send prompt to AI service."""
        try:
            url = f"{env_settings.AI_SERVICE_URL}/api/v1/team/{job_data.get('team_id')}/stream/{thread_id}"
            logger.info(f"Sending prompt to: {url}")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-User-Id": job_data.get("user_id", ""),
                "X-User-Role": job_data.get("user_role", ""),
                "X-User-Timezone": job_data.get("user_timezone", ""),
            }

            payload = {
                "messages": [{"type": "human", "content": job_data.get("prompt", "")}]
            }

            logger.debug(f"Sending prompt to AI service with thread ID: {thread_id}")
            logger.debug(f"Prompt payload: {payload}")
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info("Successfully sent prompt to AI service")
            return response.text

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to send prompt - HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.ConnectError:
            error_msg = f"Failed to send prompt - Connection error: Unable to connect to AI service at {env_settings.AI_SERVICE_URL}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException:
            error_msg = f"Failed to send prompt - Timeout error: AI service did not respond within {env_settings.JOB_TIMEOUT} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Failed to send prompt - Request error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to send prompt - Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _update_execution_success(
        self, execution_id: str, thread_id: str, response: str, start_time: datetime
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
                    thread_id=thread_id,
                    response_received=response,
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

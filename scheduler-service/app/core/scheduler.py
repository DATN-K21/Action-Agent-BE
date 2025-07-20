import asyncio
from datetime import datetime
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from croniter import croniter
from sqlalchemy import text

from app.core import logging
from app.core.database import async_engine, sync_engine
from app.core.settings import env_settings
from app.services.job_executor import JobExecutor

logger = logging.get_logger(__name__)


async def execute_job_task(job_id: str, job_data: Dict) -> None:
    """Module-level function to execute a job (for APScheduler serialization)."""
    job_executor = JobExecutor()
    try:
        await job_executor.execute_job(job_id, job_data)
    except Exception as e:
        logger.exception(f"Job execution failed for {job_id}: {str(e)}")
    finally:
        await job_executor.close()


class SchedulerManager:
    """Manages the APScheduler instance and job operations."""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        # Ensure schema exists before starting scheduler
        await self._ensure_schema_exists()
        
        # Configure job stores - using SQLAlchemy instead of Redis
        jobstores = {
            'default': SQLAlchemyJobStore(
                engine=sync_engine,
                tablename=f'{env_settings.POSTGRES_SCHEMA}.apscheduler_jobs'
            )
        }
        
        # Configure executors
        executors = {"default": AsyncIOExecutor()}
        
        # Job defaults
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 30
        }
        
        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=env_settings.SCHEDULER_TIMEZONE
        )
        
        # Start scheduler
        self.scheduler.start()
        self._running = True

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return
        
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None

        self._running = False
    
    async def add_job(
        self,
        job_id: str,
        cron_expression: str,
        job_data: Dict,
        timezone: str,
    ) -> bool:
        """Add a job to the scheduler."""
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            # Validate cron expression
            if not self.is_valid_cron(cron_expression):
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=execute_job_task,
                trigger='cron',
                id=job_id,
                args=[job_id, job_data],
                **self._parse_cron_expression(cron_expression),
                timezone=timezone,
                replace_existing=True
            )
            
            logger.info(f"Job {job_id} added to scheduler")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to add job {job_id}: {str(e)}")
            return False
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed from scheduler")
            return True
        except Exception as e:
            logger.exception(f"Failed to remove job {job_id}: {str(e)}")
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job {job_id} paused")
            return True
        except Exception as e:
            logger.exception(f"Failed to pause job {job_id}: {str(e)}")
            return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job {job_id} resumed")
            return True
        except Exception as e:
            logger.exception(f"Failed to resume job {job_id}: {str(e)}")
            return False
    
    async def run_job_now(self, job_id: str, job_data: Dict) -> bool:
        """Run a job immediately."""
        try:
            # Execute job in background
            asyncio.create_task(execute_job_task(job_id, job_data))
            logger.info(f"Job {job_id} triggered manually")
            return True
        except Exception as e:
            logger.exception(f"Failed to run job {job_id}: {str(e)}")
            return False
    

    
    def is_valid_cron(self, cron_expression: str) -> bool:
        """Validate a cron expression."""
        try:
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def _parse_cron_expression(self, cron_expression: str) -> Dict:
        """Parse cron expression into APScheduler format."""
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression format")
        
        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }

    def get_next_run_time(
        self, cron_expression: str, timezone_str: str
    ) -> Optional[datetime]:
        """Get the next run time (naive datetime in local time) for a cron expression."""
        try:
            tzinfo = ZoneInfo(timezone_str)
            base_time = datetime.now(tzinfo)  # offset-aware
            cron = croniter(cron_expression, base_time)
            next_time_aware = datetime.fromtimestamp(cron.get_next(), tz=tzinfo)
            next_time_naive = next_time_aware.replace(
                tzinfo=None
            )  # convert to naive datetime
            return next_time_naive
        except Exception:
            return None
    
    async def _ensure_schema_exists(self) -> None:
        """Ensure the PostgreSQL schema exists for APScheduler tables."""
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {env_settings.POSTGRES_SCHEMA}"))
            logger.info(f"Schema '{env_settings.POSTGRES_SCHEMA}' ready")
        except Exception as e:
            logger.exception(
                f"Failed to create schema '{env_settings.POSTGRES_SCHEMA}': {str(e)}"
            )
            raise


# Global scheduler manager instance
scheduler_manager = SchedulerManager()

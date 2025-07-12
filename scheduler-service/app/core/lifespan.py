from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core import logging
from app.core.database import close_db_connections, init_db
from app.core.scheduler import scheduler_manager

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with proper resource cleanup."""
    logger.info("Starting scheduler service...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Start scheduler
        await scheduler_manager.start()
        logger.info("Scheduler started")
        
        yield
        
    finally:
        # Shutdown in reverse order
        logger.info("Shutting down scheduler service...")
        
        # Stop scheduler first
        try:
            await scheduler_manager.stop()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        # Then close database connections
        try:
            await close_db_connections()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
        
        logger.info("Scheduler service shutdown completed")

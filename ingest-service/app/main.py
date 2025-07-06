"""
Main module for the ingest-service. This is just a wrapper to import the celery app.
"""

from celery import Celery, signals
from kombu import Queue

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


@signals.after_setup_logger.connect
def _update_root_logger(logger, *args, **kwargs):
    logger.setLevel(env_settings.LOGGING_LOG_LEVEL)  # global “celery” logger
    for h in logger.handlers:  # keep handlers in sync
        h.setLevel(env_settings.LOGGING_LOG_LEVEL)


@signals.after_setup_task_logger.connect
def _update_task_logger(logger, *args, **kwargs):
    logger.setLevel(env_settings.LOGGING_LOG_LEVEL)  # per-task logger


celery_app = Celery(
    "ingest-service",
    broker=env_settings.RABBITMQ_URL,
    backend=env_settings.REDIS_URL,
    include=["app.core.tasks"],
)

celery_app.conf.update(
    result_expires=3600,
    task_acks_late=True,  # Enable late acknowledgment for better reliability
    worker_prefetch_multiplier=1,  # Process one task at a time for load balancing
    task_reject_on_worker_lost=True,  # Reject tasks if worker is lost
)

# Configure worker to consume from specific queues by default
# This tells Celery which queues to consume from when no -Q is specified
celery_app.conf.task_queues = (
    Queue("document.processing"),
    Queue("document.search"),
    Queue("ping"),
)

celery_app.conf.update(task_track_started=True)

# Configure Celery logging
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

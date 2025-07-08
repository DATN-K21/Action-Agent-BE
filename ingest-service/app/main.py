from app.core import logging

logging.configure_logging()

from celery import Celery
from kombu import Queue

from app.core.settings import env_settings

logger = logging.get_logger(__name__)


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
    Queue("ping"),
)

celery_app.conf.update(task_track_started=True)

# Configure Celery logging
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from celery import Celery

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


celery_app = Celery(
    "aiservice",
    broker=env_settings.RABBITMQ_URL,
    backend=env_settings.REDIS_URL,
    # No tasks included - ai-service only sends tasks to other services
)

celery_app.conf.update(
    result_expires=60 * 60 * 4,  # 4 hours
    task_acks_late=True,  # Enable late acknowledgment for better reliability
)

# Task routes removed as queue is explicitly specified in each send_task call
celery_app.conf.update(task_track_started=True)

# Configure Celery logging
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

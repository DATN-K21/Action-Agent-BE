import logging
import sys

import structlog
from celery import signals
from structlog.stdlib import BoundLogger

from app.core.settings import env_settings


def configure_logging():
    """Configures structured logging with clean, colored, non-duplicated logs"""

    # Clear any existing handlers
    logging.root.handlers.clear()

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(env_settings.LOGGING_LOG_LEVEL),
        context_class=dict,
    )

    # Ensure standard logging uses structlog
    handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format="%(message)s", level=env_settings.LOGGING_LOG_LEVEL, handlers=[handler])
    logging.getLogger().handlers = [handler]

    @signals.after_setup_logger.connect
    def _update_root_logger(logger, *args, **kwargs):
        logger.setLevel(env_settings.LOGGING_LOG_LEVEL)  # global “celery” logger
        for h in logger.handlers:  # keep handlers in sync
            h.setLevel(env_settings.LOGGING_LOG_LEVEL)

    @signals.after_setup_task_logger.connect
    def _update_task_logger(logger, *args, **kwargs):
        logger.setLevel(env_settings.LOGGING_LOG_LEVEL)  # per-task logger


def get_logger(name: str) -> BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)

import logging
import sys

import structlog
from structlog.stdlib import BoundLogger

from app.core.settings import env_settings


def configure_logging():
    """Configures structured logging with clean, colored, non-duplicated logs"""

    # Clear any existing handlers
    logging.root.handlers.clear()

    # Disable Uvicorn default loggers to prevent duplicate logs
    uvicorn_loggers = ["uvicorn", "uvicorn.access", "uvicorn.error"]
    for name in uvicorn_loggers:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = False  # Important to prevent bubble-up

    # Disable HTTP request logs from external libraries
    http_loggers = ["openai", "httpx", "anthropic", "httpcore", "numexpr", "azure.storage.blob"]
    for name in http_loggers:
        http_logger = logging.getLogger(name)
        http_logger.setLevel(logging.WARNING)  # Only show warnings and errors
        http_logger.propagate = False

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
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


def get_logger(name: str) -> BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)

import logging
from functools import wraps
from typing import Any

import structlog
from elasticsearch import Elasticsearch
from structlog.processors import TimeStamper, format_exc_info

from app.core.settings import env_settings
from app.utils.logging import is_async, is_method


def configure_logging():
    timestamper = TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        timestamper,
        format_exc_info,
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]

    structlog.configure(
        processors=shared_processors + [structlog.dev.ConsoleRenderer()],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=getattr(logging, env_settings.LOG_LEVEL.upper()))

    if env_settings.LOG_TO_ELASTICSEARCH:
        es_client = Elasticsearch(
            env_settings.ELASTICSEARCH_URL,
            basic_auth=(env_settings.ELASTICSEARCH_USER, env_settings.ELASTICSEARCH_PASSWORD),
            verify_certs=False,
        )

        class ElasticsearchLogHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                log_entry_dict = {"message": log_entry}
                es_client.index(index="app-logs", document=log_entry_dict)

        es_handler = ElasticsearchLogHandler()
        es_handler.setLevel(getattr(logging, env_settings.LOG_LEVEL.upper()))
        es_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(es_handler)


# Sanitize args and kwargs for logging
def sanitize_args(args, kwargs, skip_first_arg=False):
    """Sanitize args and kwargs for logging."""
    if skip_first_arg:
        args = args[1:]  # Skip 'self' or 'cls'
    return {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()},
    }


def get_logger(name: str) -> Any:
    """Get a logger instance."""
    return structlog.get_logger(name)


def log_function_inputs(logger):
    """Decorator to log function inputs."""

    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Wrapper for synchronous functions."""
            bound_logger = logger.bind(**sanitize_args(args, kwargs, is_method(func)))
            bound_logger.info(f"{func.__name__} =>")
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Wrapper for asynchronous functions."""
            bound_logger = logger.bind(**sanitize_args(args, kwargs, is_method(func)))
            bound_logger.info(f"{func.__name__} =>")
            return await func(*args, **kwargs)

        return async_wrapper if is_async(func) else sync_wrapper

    return decorator

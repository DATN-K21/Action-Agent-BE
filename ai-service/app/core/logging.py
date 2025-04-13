import logging
import sys
from functools import lru_cache, wraps
from inspect import iscoroutinefunction, signature

import structlog
from structlog.stdlib import BoundLogger

from app.core.settings import env_settings


@lru_cache(maxsize=None)  # Infinite caching for coroutine checks
def _is_async(func):
    """Check if a function is asynchronous."""
    return iscoroutinefunction(func)


@lru_cache(maxsize=None)  # Infinite caching for method checks
def _is_method(func):
    """Check if a function is a method (instance or class method)."""
    sig = signature(func)
    return "self" in sig.parameters or "cls" in sig.parameters


def _sanitize_args(args, kwargs, skip_first_arg=False):
    """Sanitize args and kwargs for logging."""
    if skip_first_arg:
        args = args[1:]  # Skip 'self' or 'cls'
    return {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()},
    }


def configure_logging():
    """Configures structured logging with clean, colored, non-duplicated logs"""

    # Clear any existing handlers
    logging.root.handlers.clear()

    # Disable Uvicorn default loggers to prevent duplicate logs
    # uvicorn_loggers = ["uvicorn", "uvicorn.access", "uvicorn.error"]
    # for name in uvicorn_loggers:
    #     uvicorn_logger = logging.getLogger(name)
    #     uvicorn_logger.handlers.clear()
    #     uvicorn_logger.propagate = False  # Important to prevent bubble-up

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
        wrapper_class=structlog.make_filtering_bound_logger(env_settings.LOG_LEVEL),
        context_class=dict,
    )

    # Ensure standard logging uses structlog
    handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format="%(message)s", level=env_settings.LOG_LEVEL, handlers=[handler])
    logging.getLogger().handlers = [handler]



def get_logger(name: str) -> BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)


def log_function_inputs(logger):
    """Decorator to log function inputs."""

    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Wrapper for synchronous functions."""
            bound_logger = logger.bind(**_sanitize_args(args, kwargs, _is_method(func)))
            bound_logger.info(f"{func.__name__} =>")
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Wrapper for asynchronous functions."""
            bound_logger = logger.bind(**_sanitize_args(args, kwargs, _is_method(func)))
            bound_logger.info(f"{func.__name__} =>")
            return await func(*args, **kwargs)

        return async_wrapper if _is_async(func) else sync_wrapper

    return decorator

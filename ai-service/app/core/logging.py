import logging
import sys
from functools import wraps

import structlog
from structlog.stdlib import BoundLogger

from app.core.utils.logging_helpers import is_async, is_method


def configure_logging():
    """Configures structured logging with clean, colored, non-duplicated logs"""

    # 🔥 Prevent FastAPI from adding duplicate logs
    logging.root.handlers.clear()

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),  # Adds timestamp
            structlog.stdlib.add_log_level,  # Adds log level (INFO, ERROR)
            structlog.stdlib.add_logger_name,  # Adds logger name
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),  # Optional: Keeps minimal file info without rich traceback
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
    )

    # Ensure standard logging uses structlog
    logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])

    # Redirect standard logging to structlog
    logging.getLogger().handlers = [logging.StreamHandler(sys.stdout)]


# Sanitize args and kwargs for logging
def sanitize_args(args, kwargs, skip_first_arg=False):
    """Sanitize args and kwargs for logging."""
    if skip_first_arg:
        args = args[1:]  # Skip 'self' or 'cls'
    return {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()},
    }


def get_logger(name: str) -> BoundLogger:
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

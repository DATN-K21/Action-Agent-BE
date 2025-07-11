import logging
import sys
from typing import Any, Dict

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request(request_data: Dict[str, Any]) -> None:
    """Log incoming request data."""
    logger = get_logger("request")
    logger.info("Incoming request", **request_data)


def log_response(response_data: Dict[str, Any]) -> None:
    """Log outgoing response data."""
    logger = get_logger("response")
    logger.info("Outgoing response", **response_data)

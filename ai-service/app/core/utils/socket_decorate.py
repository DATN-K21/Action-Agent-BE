import functools

from pydantic import ValidationError

from app.core import logging

logger = logging.get_logger(__name__)


def validate_event(event_type):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, sid, data):
            try:
                validated_data = event_type(**data)  # Validate data using Pydantic model
                return await func(self, sid, validated_data)
            except ValidationError:
                raise

        return wrapper

    return decorator

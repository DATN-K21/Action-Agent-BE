from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core import logging
from app.core.settings import env_settings
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)


def handle_exceptions(exc: Exception):
    match exc:
        case RequestValidationError() as exc:
            status_code = 400
            first_error = exc.errors()[0]
            field = ".".join(str(x) for x in first_error["loc"])
            message = first_error["msg"]
            formatted_message = f'Validation error - "{field}": {message}'
            logger.warning(f"Validation error: {formatted_message}", errors=exc.errors())
        case ValueError() as exc:
            status_code = 400
            formatted_message = str(exc)
            logger.warning(f"Value error: {formatted_message}")
        case HTTPException() as exc:
            status_code = exc.status_code
            formatted_message = exc.detail
            logger.warning(f"HTTP exception: {formatted_message}")
        case Exception() as exc:
            status_code = 500
            formatted_message = "Internal server error"
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        case _:
            status_code = 500
            formatted_message = "Internal server error"
            logger.error("Unhandled exception: Unknown error", exc_info=True)

    return ResponseWrapper.wrap(status=status_code, message=formatted_message, data=None).to_response()


log_level = env_settings.LOG_LEVEL


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions globally.
    This middleware catches exceptions raised during request processing and logs them.
    It also formats the response to return a consistent error message.
    """

    async def dispatch(self, request: Request, handler: RequestResponseEndpoint) -> Response:
        if log_level == "DEBUG":
            start_at = datetime.now()
        try:
            response = await handler(request)
            return response
        except Exception as exc:
            return handle_exceptions(exc)
        finally:
            if log_level == "DEBUG":
                ended_at = datetime.now()
                logger.debug(f"Request done: {(ended_at - start_at).total_seconds():.2f} second(s)")


def exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handle exceptions raised during request processing.
    This function is called when an exception occurs in the application.
    """
    return handle_exceptions(exc)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup the exception handler for the FastAPI application.
    This function is called during the application startup.
    """
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_exception_handler(RequestValidationError, exception_handler)
    app.add_exception_handler(HTTPException, exception_handler)
    app.add_exception_handler(Exception, exception_handler)

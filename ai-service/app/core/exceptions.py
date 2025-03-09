from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core import logging
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)


def register_exception_handlers(app: FastAPI):
    """Register all custom exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Custom validation error response"""
        first_error = exc.errors()[0]
        field = ".".join(str(x) for x in first_error["loc"])
        message = first_error["msg"]
        formatted_message = f'Validation error - "{field}": {message}'
        logger.error(f"Validation error in {request.method} {request.url.path}", errors=exc.errors())
        return ResponseWrapper.wrap(status=400, message=formatted_message, data=None).to_response()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom HTTP exception handler"""
        logger.error(f"HTTP exception in {request.method} {request.url.path}: {str(exc)}")
        return ResponseWrapper.wrap(status=exc.status_code, message=exc.detail, data=None).to_response()

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Custom global exception handler"""
        logger.exception(f"Global exception in {request.method} {request.url.path}: {str(exc)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error", data=None).to_response()

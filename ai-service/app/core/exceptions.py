from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from app.core import logging
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        "HTTP exception occurred", method=request.method, url=request.url.path, status_code=exc.status_code, detail=exc.detail
    )
    return ResponseWrapper(status=500, message=exc.detail, data=None).to_response()


# Global Exception Handler for ValidationError (from Pydantic)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error("Validation error", method=request.method, url=request.url.path, errors=exc.errors())
    return ResponseWrapper(status=400, message="Validation error", data=None).to_response()


# Global Catch-all Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=request.url.path,
        exception=str(exc),
    )
    return ResponseWrapper(status=500, message="Internal server error", data=None).to_response()


@app.get("/error")
def raise_error():
    raise Exception("This is an exception")

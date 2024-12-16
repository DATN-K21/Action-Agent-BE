import os
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api import router
from app.life_span import lifespan
from app.utils.exceptions import ExecutingException
from app.models.response_models import ExceptionResponse

logger = logging.getLogger(__name__)
app = FastAPI(
    debug=os.getenv("DEBUG", False),
    title="Action-Executing AI Service API",
    description="This is a AI SERVICE API using FastAPI and Swagger UI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={
            "status": 400,
            "message": "Validation error occurred",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("An unexpected error occurred.", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "An unexpected error occurred."
        }
    )

@app.exception_handler(ExecutingException)
async def executing_exception_handler(request: Request, e: ExecutingException):
    return JSONResponse(
        status_code=200,
        content= ExceptionResponse(
            status=500,
            message=e.output,
            errorStack=e.detail
        ).model_dump()
    )
app.include_router(router)

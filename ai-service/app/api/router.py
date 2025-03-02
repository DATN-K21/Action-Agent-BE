from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.routes import agent, callback, extension, history, multi_agent, test, thread, upload, user


class ValidationErrorResponse(BaseModel):
    status: int = 400
    message: str = "Validation Error - {field}: {message}"
    data: Any = None


router = APIRouter(
    responses={
        400: {
            "model": ValidationErrorResponse,
            "description": "Validation Error",
        }
    }
)

router.include_router(test.router, prefix="", tags=["General"])

router.include_router(callback.router, prefix="/callback", tags=["Callback"], include_in_schema=False)

router.include_router(extension.router, prefix="/extension", tags=["Extension"])

router.include_router(agent.router, prefix="/agent", tags=["Agent"])

router.include_router(multi_agent.router, prefix="/multi_agent", tags=["Multi agent"])

router.include_router(history.router, prefix="/history", tags=["History"])

router.include_router(upload.router, prefix="/upload", tags=["Upload"])

router.include_router(user.router, prefix="/user", tags=["User"])

router.include_router(thread.router, prefix="/thread", tags=["Thread"])

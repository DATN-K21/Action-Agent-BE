from fastapi import APIRouter
from pydantic import BaseModel

from app.api.internal import user as internal_user
from app.api.public.v1 import assistant, callback, connected_extension, connected_mcp, extension, test, thread, user


class ValidationErrorResponse(BaseModel):
    status: int = 400
    message: str = "Validation Error - {field}: {message}"


validation_error_responses: dict = {
    400: {
        "model": ValidationErrorResponse,
        "description": "Validation Error",
    }
}

router = APIRouter(responses=validation_error_responses)

# Ping routes
router.include_router(test.router)

# Private routes
private_router = APIRouter(prefix="/private", tags=["Private"])
private_router.include_router(internal_user.router)
router.include_router(private_router)

# Public routes v1
prefix = "/api/v1"
router.include_router(callback.router, prefix=prefix)

router.include_router(thread.router, prefix=prefix)

router.include_router(extension.router, prefix=prefix)
router.include_router(user.router, prefix=prefix)
router.include_router(connected_mcp.router, prefix=prefix)

# Public routes v2
prefix = "/api/v2"
# router.include_router(mcp_agent.router, prefix=prefix)
router.include_router(assistant.router, prefix=prefix)
router.include_router(connected_extension.router, prefix=prefix)

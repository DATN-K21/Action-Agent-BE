from fastapi import APIRouter
from pydantic import BaseModel

from app.api.internal import user as internal_user
from app.api.public import agent, callback, connected_app, extension, multi_agent, test, thread


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

# Public routes
router.include_router(test.router)
router.include_router(callback.router)

router.include_router(thread.router)
router.include_router(connected_app.router)

router.include_router(agent.router)
router.include_router(multi_agent.router)
router.include_router(extension.router)


# Private routes
private_router = APIRouter(prefix="/private", tags=["Private"])
private_router.include_router(internal_user.router)
router.include_router(private_router)

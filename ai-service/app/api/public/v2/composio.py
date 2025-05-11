from fastapi import APIRouter

from app.schemas.base import ResponseWrapper
from app.schemas.composio_client import (
    GetAllAppsComposioResponse,
)
from app.services.composio.composio_client import ComposioClient

router = APIRouter(prefix="/composio", tags=["API-V2 | Composio Client"])


@router.get("/apps", summary="Get all apps.", response_model=ResponseWrapper[GetAllAppsComposioResponse])
def get_all_apps():
    response = ComposioClient.get_all_apps()
    if not response.success:
        return ResponseWrapper.wrap(
            status=500,
            message=response.message,
        ).to_response()

    return ResponseWrapper.wrap(
        status=200,
        message="Get all apps successfully",
        data=response,
    ).to_response()

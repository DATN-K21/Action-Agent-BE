from fastapi import APIRouter

from app.schemas.base import ResponseWrapper
from app.schemas.composio_client import (
    FilterComposioAppEnumsResponse,
    FilterComposioAppsResponse,
    GetAllAppsComposioEnumsResponse,
    GetAllAppsComposioResponse,
    GetSingleAppComposioResponse,
)
from app.services.composio.composio_client import ComposioClient

router = APIRouter(prefix="/composio", tags=["API-V2 | Composio Client"])

# Get all apps
@router.get("/apps", summary="Get all apps.", response_model=ResponseWrapper[GetAllAppsComposioResponse])
def get_all_apps():
    response = ComposioClient.get_all_apps()
    if not response.success:
        return ResponseWrapper.wrap(
            status=500,
            message=response.message,
        ).to_response()

    returned_data = FilterComposioAppsResponse(
        items=response.items,
        count=response.count,
    )

    return ResponseWrapper.wrap(
        status=200,
        message="Get all apps successfully",
        data=returned_data,
    ).to_response()

# Get single app
@router.get("/apps/{app_enum}", summary="Get single app.", response_model=ResponseWrapper[GetSingleAppComposioResponse])
def get_single_app(app_enum: str):
    response = ComposioClient.get_single_app(app_enum=app_enum)
    if not response.success or response.data is None:
        return ResponseWrapper.wrap(
            status=500,
            message=response.message,
        ).to_response()

    return ResponseWrapper.wrap(
        status=200,
        message="Get single app successfully",
        data=response.data,
    ).to_response()


# Get all app enums
@router.get("/apps/list/enums", summary="Get all app enums.", response_model=ResponseWrapper[GetAllAppsComposioEnumsResponse])
def get_all_app_enums():
    response = ComposioClient.get_all_app_enums()
    if not response.success:
        return ResponseWrapper.wrap(
            status=500,
            message=response.message,
        ).to_response()

    returned_data = FilterComposioAppEnumsResponse(
        items=response.items,
        count=response.count,
    )

    return ResponseWrapper.wrap(
        status=200,
        message="Get all app enums successfully",
        data=returned_data,
    ).to_response()
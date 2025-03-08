from fastapi import APIRouter, Depends

from app.core import logging
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.connected_app import GetConnectedAppResponse, GetAllConnectedAppsRequest
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.deps import get_connected_app_service

logger = logging.get_logger(__name__)

router = APIRouter()


@router.get("/{user_id}/{extension_name}/get-detail", response_model=ResponseWrapper[GetConnectedAppResponse])
async def get_detail(
        user_id: str,
        extension_name: str,
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    response_data = await connected_app_service.get_connected_app(user_id, extension_name)
    if response_data is None:
        return ResponseWrapper.wrap(status=404, message="Connected app not found").to_response()

    return ResponseWrapper.wrap(status=200, data=response_data).to_response()


@router.get("/{user_id}/get-all", response_model=ResponseWrapper[GetAllConnectedAppsRequest])
async def get_all(
        user_id: str,
        paging: PagingRequest = Depends(),
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    response_data = await connected_app_service.get_all_connected_apps(
        user_id=user_id,
        paging=paging
    )
    return ResponseWrapper.wrap(status=200, data=response_data).to_response()

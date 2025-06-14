from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.connected_app import GetConnectedAppsResponse, GetConnectedAppResponse
from app.services.database.connected_app_service import ConnectedAppService, get_connected_app_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/connected-app", tags=["Connected App"])


@router.get("/{user_id}/get-all", summary="Get all connections.",
            response_model=ResponseWrapper[GetConnectedAppsResponse])
async def get_all(
        user_id: str,
        paging: PagingRequest = Depends(),
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_app_service.list_connected_apps(user_id=user_id, paging=paging)
    return response.to_response()


@router.get("/{user_id}/{extension_name}/get-detail", summary="Get detail connection.",
            response_model=ResponseWrapper[GetConnectedAppResponse])
async def get_detail(
        user_id: str,
        extension_name: str,
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_app_service.get_connected_app(user_id, extension_name)
    return response.to_response()

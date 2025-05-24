from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.connected_extension import GetConnectedExtensionsResponse, GetConnectedExtensionResponse
from app.services.database.connected_extension_service import get_connected_extension_service, ConnectedExtensionService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/connected-extension", tags=["API-V2 | Connected Extension"])


@router.get("/{user_id}/get-all", summary="Get all connections.",
            response_model=ResponseWrapper[GetConnectedExtensionsResponse])
async def get_all(
        user_id: str,
        paging: PagingRequest = Depends(),
        connected_service_service: ConnectedExtensionService = Depends(get_connected_extension_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_service_service.list_connected_extensions(user_id=user_id, paging=paging)
    return response.to_response()


@router.get("/{user_id}/{extension_id}/get-detail", summary="Get detail connection.",
            response_model=ResponseWrapper[GetConnectedExtensionResponse])
async def get_detail(
        user_id: str,
        extension_id: str,
        connected_service_service: ConnectedExtensionService = Depends(get_connected_extension_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_service_service.get_connected_extension_by_id(user_id, extension_id)
    return response.to_response()

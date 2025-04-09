from fastapi import APIRouter, Depends

from app.api.deps import ensure_user_id
from app.core import logging
from app.schemas.base import ResponseWrapper
from app.schemas.user_api_key import (
    DeleteApiKeyRequest,
    DeleteApiKeyResponse,
    GetApiKeyResponse,
    SetDefaultApiKeyRequest,
    SetDefaultApiKeyResponse,
    UpsertApiKeyRequest,
    UpsertApiKeyResponse,
)
from app.services.database.deps import get_user_service
from app.services.database.user_service import UserService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/{user_id}/key/get-all", summary="Get API Keys.", response_model=ResponseWrapper[GetApiKeyResponse])
async def get_api_key(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_user_id),
):
    response = await user_service.get_user_with_api_keys(user_id)
    return response.to_response()


@router.post("/{user_id}/key/set-default", summary="Set default API Key.", response_model=ResponseWrapper[SetDefaultApiKeyResponse])
async def set_default_api_key(
    user_id: str,
    request: SetDefaultApiKeyRequest,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_user_id),
):
    response = await user_service.set_default_api_key(user_id, request.provider)
    return response.to_response()


@router.put("/{user_id}/key/upsert", summary="Upsert API Key.", response_model=ResponseWrapper[UpsertApiKeyResponse])
async def upsert_api_key(
    user_id: str,
    request: UpsertApiKeyRequest,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_user_id),
):
    response = await user_service.upsert_api_key(user_id, request.provider, request.encrypted_value)
    return response.to_response()

@router.delete("/{user_id}/key/delete", summary="Delete API Key.", response_model=ResponseWrapper[DeleteApiKeyResponse])
async def delete_api_key(
    user_id: str,
    request: DeleteApiKeyRequest,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_user_id),
):
    response = await user_service.delete_api_key(user_id, request.provider)
    return response.to_response()

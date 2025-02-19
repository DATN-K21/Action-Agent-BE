from fastapi import APIRouter, Depends

from app.core import logging
from app.dependencies import get_identity_service, get_user_service
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetListUsersResponse,
    GetUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)
from app.services.database.user_service import UserService
from app.services.identity_service import IdentityService

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/create", response_model=ResponseWrapper[CreateUserResponse])
async def create_new_user(
    user: CreateUserRequest,
    user_service: UserService = Depends(get_user_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if not identity_service.is_admin():
        return ResponseWrapper(status=403, message="Forbidden").to_response()
    response = await user_service.create_user(user)
    return response.to_response()


@router.get("/{user_id}/get-detail", response_model=ResponseWrapper[GetUserResponse])
async def get_user_by_user_id(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if not identity_service.is_admin() and identity_service.user_id() != user_id:
        return ResponseWrapper(status=403, message="Forbidden").to_response()
    response = await user_service.get_user_by_id(user_id)
    return response.to_response()


@router.get("/get-all", response_model=ResponseWrapper[GetListUsersResponse])
async def get_all_users(
    paging: PagingRequest = Depends(),
    user_service: UserService = Depends(get_user_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if not identity_service.is_admin():
        return ResponseWrapper(status=403, message="Forbidden").to_response()
    response = await user_service.get_all_users(paging)
    return response.to_response()


@router.patch("/{user_id}/update", response_model=ResponseWrapper[UpdateUserResponse])
async def update_user(
    user_id: str,
    user: UpdateUserRequest,
    user_service: UserService = Depends(get_user_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if not identity_service.is_admin() and identity_service.user_id() != user_id:
        return ResponseWrapper(status=403, message="Forbidden").to_response()
    response = await user_service.update_user(user_id, user)
    return response.to_response()


@router.delete("/{user_id}", response_model=ResponseWrapper[DeleteUserResponse])
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if not identity_service.is_admin():
        return ResponseWrapper(status=403, message="Forbidden").to_response()
    response = await user_service.delete_user(user_id)
    return response.to_response()

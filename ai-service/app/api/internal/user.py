from fastapi import APIRouter, Depends

from app.core import logging
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
from app.services.database.deps import get_user_service
from app.services.database.user_service import UserService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/create", summary="Create a new user.", response_model=ResponseWrapper[CreateUserResponse])
async def create_new_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.create_user(request)
    return response.to_response()


@router.patch("/{user_id}/update", summary="Update the given user.", response_model=ResponseWrapper[UpdateUserResponse])
async def update_user(
    user_id: str,
    user: UpdateUserRequest,
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.update_user(user_id, user)
    return response.to_response()


@router.delete("/{user_id}/delete", summary="Delete the given user.", response_model=ResponseWrapper[DeleteUserResponse])
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.delete_user(user_id)
    return response.to_response()


@router.get("/get-all", summary="Get all users.", response_model=ResponseWrapper[GetListUsersResponse])
async def get_all_users(
    paging: PagingRequest = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.get_all_users(paging)
    return response.to_response()


@router.get("/{user_id}/get-detail", summary="Get details of the given user.", response_model=ResponseWrapper[GetUserResponse])
async def get_user_by_user_id(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.get_user_by_id(user_id)
    return response.to_response()
from fastapi import APIRouter, Depends

from app.api.deps import ensure_admin, ensure_user_id
from app.core import logging
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.user import (
    GetListUsersResponse,
    GetUserResponse,
)
from app.services.database.deps import get_user_service
from app.services.database.user_service import UserService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/get-all", summary="Get all users.", response_model=ResponseWrapper[GetListUsersResponse])
async def get_all_users(
    paging: PagingRequest = Depends(),
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_admin),
):
    response = await user_service.get_all_users(paging)
    return response.to_response()


@router.get("/{user_id}/get-detail", summary="Get details of the given user.", response_model=ResponseWrapper[GetUserResponse])
async def get_user_by_user_id(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(ensure_user_id),
):
    response = await user_service.get_user_by_id(user_id)
    return response.to_response()


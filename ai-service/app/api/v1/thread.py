from fastapi import APIRouter, Depends

from app.core import logging
from app.dependencies import get_identity_service, get_thread_service
from app.schemas.base import CursorPagingRequest, ResponseWrapper
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    DeleteThreadResponse,
    GetListThreadsResponse,
    GetThreadResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
)
from app.services.database.thread_service import ThreadService
from app.services.identity_service import IdentityService

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/create", response_model=ResponseWrapper[CreateThreadResponse])
async def create_new_thread(
    request: CreateThreadRequest,
    thread_service: ThreadService = Depends(get_thread_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    response = await thread_service.create_thread(request, identity_service.user_id())
    return response.to_response()


@router.get("/{user_id}/{thread_id}/get-detail", response_model=ResponseWrapper[GetThreadResponse])
async def get_thread_by_id(
    user_id: str,
    thread_id: str,
    thread_service: ThreadService = Depends(get_thread_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    if not identity_service.is_same_user(user_id) and not identity_service.is_admin():
        return ResponseWrapper.wrap(status=403, message="Forbidden")
    response = await thread_service.get_thread_by_id(user_id, thread_id)
    return response.to_response()


@router.post("/{user_id}/get-all", response_model=ResponseWrapper[GetListThreadsResponse])
async def get_all_threads(
    user_id: str,
    paging: CursorPagingRequest = Depends(),
    thread_service: ThreadService = Depends(get_thread_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    if not identity_service.is_same_user(user_id) and not identity_service.is_admin():
        return ResponseWrapper.wrap(status=403, message="Forbidden")
    response = await thread_service.get_all_threads(user_id, paging)
    return response.to_response()


@router.patch("/{user_id}/{thread_id}/update", response_model=ResponseWrapper[UpdateThreadResponse])
async def update_thread(
    user_id: str,
    thread_id: str,
    thread: UpdateThreadRequest,
    thread_service: ThreadService = Depends(get_thread_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    if not identity_service.is_same_user(user_id) and not identity_service.is_admin():
        return ResponseWrapper.wrap(status=403, message="Forbidden")
    response = await thread_service.update_thread(user_id, thread_id, thread)
    return response.to_response()


@router.delete("/{user_id}/{thread_id}", response_model=ResponseWrapper[DeleteThreadResponse])
async def delete_thread(
    user_id: str,
    thread_id: str,
    thread_service: ThreadService = Depends(get_thread_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    if identity_service.is_admin():
        response = await thread_service.delete_thread(user_id, thread_id)
    elif identity_service.is_same_user(user_id):
        response = await thread_service.delete_thread(user_id, thread_id, user_id)
    else:
        return ResponseWrapper.wrap(status=403, message="Forbidden")
    return response.to_response()

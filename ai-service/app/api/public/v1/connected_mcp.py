from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.connected_mcp import CreateConnectedMcpResponse
from app.schemas.connected_mcp import GetConnectedMcpsResponse, CreateConnectedMcpRequest, GetConnectedMcpResponse, \
    UpdateConnectedMcpRequest, DeleteConnectedMcpResponse
from app.schemas.thread import (
    UpdateThreadResponse,
)
from app.services.database.connected_mcp_service import ConnectedMcpService, get_connected_mcp_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/{user_id}/get-all", summary="Get all connected mcps of a user.",
            response_model=ResponseWrapper[GetConnectedMcpsResponse])
async def get_all_connected_mcps(
        user_id: str,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        paging: PagingRequest = Depends(),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_mcp_service.get_all_connected_mcps(user_id, paging)
    return response.to_response()


@router.post("/{user_id}/create", summary="Create a new mcp.",
             response_model=ResponseWrapper[CreateConnectedMcpResponse])
async def create_new_thread(
        user_id: str,
        request: CreateConnectedMcpRequest,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_mcp_service.create_connected_mcp(
        user_id=user_id,
        mcp_name=request.mcp_name,
        url=request.url,
        connection_type=request.connection_type,
    )
    return response.to_response()


@router.get("/{user_id}/{connected_mcp_id}/get-detail", summary="Get connected mcp details.",
            response_model=ResponseWrapper[GetConnectedMcpResponse])
async def get_connected_mcp(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_mcp_service.get_connected_mcp(user_id, connected_mcp_id)
    return response.to_response()


@router.patch("/{user_id}/{connected_mcp_id}/update", summary="Update connected mcp information.",
              response_model=ResponseWrapper[UpdateThreadResponse])
async def update_(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp: UpdateConnectedMcpRequest,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_mcp_service.update_connected_mcp(user_id, connected_mcp_id, connected_mcp)
    return response.to_response()


@router.delete("/{user_id}/{connected_mcp_id}/delete", summary="Delete a connected mcp.",
               response_model=ResponseWrapper[DeleteConnectedMcpResponse])
async def delete_thread(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    response = await connected_mcp_service.delete_connected_mcp(user_id, connected_mcp_id)
    return response.to_response()

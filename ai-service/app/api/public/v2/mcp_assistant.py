from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.assistant import CreateAssistantResponse
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.mcp_assistant import GetMcpsOfAssistantResponse, CreateMcpAssistantRequest, UpdateMcpAssistantResponse, \
    UpdateMcpAssistantRequest, DeleteMcpAssistantResponse
from app.services.database.mcp_assistant_service import get_mcp_assistant_service, McpAssistantService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/extension-assistant", tags=["API-V2 | Extension-Assistant"])


@router.get("/{user_id}/{assistant_id}/get-all", summary="Get MCPs of user's assistant.",
            response_model=ResponseWrapper[GetMcpsOfAssistantResponse])
async def list_extensions(
        assistant_id: str,
        paging: PagingRequest = Depends(),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await mcp_assistant_service.list_mcps_of_assistant(assistant_id=assistant_id, paging=paging)
    return response.to_response()


@router.post("/{user_id}/create", summary="Add an MCP into the assistant.",
             response_model=ResponseWrapper[CreateAssistantResponse])
async def create_new_mcp_assistant(
        request: CreateMcpAssistantRequest = Depends(),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await mcp_assistant_service.create_mcp_assistant(request)
    return response.to_response()


@router.patch("/{user_id}/{mcp_assistant_id}/update", summary="Update mcp-assistant information.",
              response_model=ResponseWrapper[UpdateMcpAssistantResponse])
async def update_mcp_assistant(
        mcp_assistant_id: str,
        mcp_assistant: UpdateMcpAssistantRequest,
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await mcp_assistant_service.update_mcp_assistant(
        extension_assistant_id=mcp_assistant_id,
        mcp_assistant=mcp_assistant
    )
    return response.to_response()


@router.delete("/{user_id}/{mcp_assistant_id}/delete", summary="Delete a mcp-assistant.",
               response_model=ResponseWrapper[DeleteMcpAssistantResponse])
async def delete_mcp_assistant(
        mcp_assistant_id: str,
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await mcp_assistant_service.delete_mcp_assistant(
        mcp_assistant_id=mcp_assistant_id
    )
    return response.to_response()

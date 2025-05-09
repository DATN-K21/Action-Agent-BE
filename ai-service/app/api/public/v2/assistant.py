from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.assistant import GetAssistantsResponse, CreateAssistantResponse, CreateAssistantRequest, \
    UpdateAssistantResponse, GetAssistantResponse, UpdateAssistantRequest, GetFullInfoAssistantResponse
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.thread import (
    DeleteThreadResponse,
)
from app.services.database.assistant_service import AssistantService, get_assistant_service
from app.services.database.connected_extension_service import ConnectedExtensionService, get_connected_extension_service
from app.services.database.connected_mcp_service import ConnectedMcpService, get_connected_mcp_service
from app.services.database.extension_assistant_service import ExtensionAssistantService, get_extension_assistant_service
from app.services.database.mcp_assistant_service import McpAssistantService, get_mcp_assistant_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/assistant", tags=["API-V2 | Assistant"])



@router.get("/{user_id}/get-all", summary="Get assistants of a user.",
            response_model=ResponseWrapper[GetAssistantsResponse])
async def list_full_info_assistants(
        user_id: str,
        paging: PagingRequest = Depends(),
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    assistants_result = await assistant_service.list_assistants(user_id, paging)
    assistants = assistants_result.data.assistants

    full_info_assistants = []

    for assistant in assistants:
        if assistant.type == "mcp":
            mcps_result = await mcp_assistant_service.list_mcps_of_assistant(assistant.id)
            mcps = mcps_result.data.mcps
            full_info_assistants.append(
                GetFullInfoAssistantResponse(
                    **assistant.model_dump(),
                    workers=mcps
                )
            )






@router.post("/{user_id}/create", summary="Create a new assistant.",
             response_model=ResponseWrapper[CreateAssistantResponse])
async def create_new_assistant(
        user_id: str,
        request: CreateAssistantRequest,
        assistant_service: AssistantService = Depends(get_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await assistant_service.create_assistant(user_id, request)
    return response.to_response()


@router.get("/{user_id}/{assistant_id}/get-detail", summary="Get assistant details.",
            response_model=ResponseWrapper[GetAssistantResponse])
async def get_assistant_by_id(
        user_id: str,
        assistant_id: str,
        assistant_service: AssistantService = Depends(get_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await assistant_service.get_assistant_by_id(user_id, assistant_id)
    return response.to_response()


@router.patch("/{user_id}/{assistant_id}/update", summary="Update assistant information.",
              response_model=ResponseWrapper[UpdateAssistantResponse])
async def update_assistant(
        user_id: str,
        assistant_id: str,
        assistant: UpdateAssistantRequest,
        assistant_service: AssistantService = Depends(get_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await assistant_service.update_assistant(user_id, assistant_id, assistant)
    return response.to_response()


@router.delete("/{user_id}/{assistant_id}/delete", summary="Delete a thread.",
               response_model=ResponseWrapper[DeleteThreadResponse])
async def delete_assistant(
        user_id: str,
        assistant_id: str,
        assistant_service: AssistantService = Depends(get_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await assistant_service.delete_assistant(user_id, assistant_id, user_id)
    return response.to_response()

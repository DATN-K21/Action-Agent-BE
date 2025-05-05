from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.assistant import CreateAssistantResponse
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.extension_assistant import CreateExtensionAssistantRequest, UpdateExtensionAssistantResponse, \
    UpdateExtensionAssistantRequest, GetExtensionsOfAssistantResponse, DeleteExtensionAssistantResponse
from app.services.database.extension_assistant_service import ExtensionAssistantService, get_extension_assistant_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/extension-assistant", tags=["API-V2 | Extension-Assistant"])


@router.get("/{user_id}/{assistant_id}/get-all", summary="Get extensions of user's assistant.",
            response_model=ResponseWrapper[GetExtensionsOfAssistantResponse])
async def list_extensions_of_assistant(
        assistant_id: str,
        paging: PagingRequest = Depends(),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await extension_assistant_service.list_extensions_of_assistant(assistant_id=assistant_id, paging=paging)
    return response.to_response()


@router.post("/{user_id}/create", summary="Add an extension into the assistant.",
             response_model=ResponseWrapper[CreateAssistantResponse])
async def create_new_extension_assistant(
        request: CreateExtensionAssistantRequest = Depends(),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await extension_assistant_service.create_extension_assistant(request)
    return response.to_response()


@router.patch("/{user_id}/{extension_assistant_id}/update", summary="Update extension-assistant information.",
              response_model=ResponseWrapper[UpdateExtensionAssistantResponse])
async def update_extension_assistant(
        extension_assistant_id: str,
        assistant: UpdateExtensionAssistantRequest,
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await extension_assistant_service.update_extension_assistant(
        extension_assistant_id=extension_assistant_id,
        extension_assistant=assistant
    )
    return response.to_response()


@router.delete("/{user_id}/{extension_assistant_id}/delete", summary="Delete an extension-assistant.",
               response_model=ResponseWrapper[DeleteExtensionAssistantResponse])
async def delete_extension_assistant(
        extension_assistant_id: str,
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    response = await extension_assistant_service.delete_extension_assistant(
        extension_assistant_id=extension_assistant_id
    )
    return response.to_response()

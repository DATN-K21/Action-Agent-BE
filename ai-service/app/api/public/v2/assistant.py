from fastapi import APIRouter, Depends

from app.api.auth import ensure_user_id
from app.core import logging
from app.schemas.assistant import CreateAssistantRequest, \
    UpdateAssistantRequest, GetFullInfoAssistantResponse, McpData, \
    ExtensionData, GetFullInfoAssistantsResponse, CreateFullInfoAssistantRequest, CreateFullInfoAssistantResponse, \
    UpdateFullInfoAssistantRequest, UpdateFullInfoAssistantResponse
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.extension_assistant import CreateExtensionAssistantRequest
from app.schemas.mcp_assistant import CreateMcpAssistantRequest
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
            response_model=ResponseWrapper[GetFullInfoAssistantsResponse])
async def list_full_info_assistants(
        user_id: str,
        paging: PagingRequest = Depends(),
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    assistants_result = await assistant_service.list_assistants(user_id, paging)

    if assistants_result.status != 200:
        return ResponseWrapper.wrap(status=assistants_result.status, message=assistants_result.message)

    assistants = assistants_result.data.assistants

    full_info_assistants = []

    for assistant in assistants:
        if assistant.type == "mcp":
            mcps_result = await mcp_assistant_service.list_mcps_of_assistant(assistant.id)

            if mcps_result.status != 200:
                return ResponseWrapper.wrap(status=mcps_result.status, message=mcps_result.message)

            mcps = [McpData(
                id=mcp.mcp_id,
                mcp_name=mcp.mcp_name,
                url=mcp.url,
                connection_type=mcp.connection_type,
                created_at=mcp.created_at,
            ) for mcp in mcps_result.data.mcps]
            full_info_assistants.append(
                GetFullInfoAssistantResponse(
                    **assistant.model_dump(),
                    workers=mcps
                )
            )
        elif assistant.type == "extension":
            extensions_result = await extension_assistant_service.list_extensions_of_assistant(assistant.id)
            if extensions_result.status != 200:
                return ResponseWrapper.wrap(status=extensions_result.status, message=extensions_result.message)

            extensions = [ExtensionData(
                id=extension.extension_id,
                extension_name=extension.extension_name,
                connected_account_id=extension.connected_account_id,
                auth_scheme=extension.auth_scheme,
                auth_value=extension.auth_value,
                created_at=extension.created_at,
            ) for extension in extensions_result.data.extensions]
            full_info_assistants.append(
                GetFullInfoAssistantResponse(
                    **assistant.model_dump(),
                    workers=extensions
                )
            )

    data = GetFullInfoAssistantsResponse(
        full_info_assistants=full_info_assistants,
        page_number=assistants_result.data.page_number,
        max_per_page=assistants_result.data.max_per_page,
        total_page=assistants_result.data.total_page,
    )

    return ResponseWrapper.wrap(status=200, data=data).to_response()


@router.post("/{user_id}/create", summary="Create a new assistant.",
             response_model=ResponseWrapper[CreateFullInfoAssistantResponse])
async def create_full_info_assistant(
        user_id: str,
        request: CreateFullInfoAssistantRequest,
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        connected_extension_service: ConnectedExtensionService = Depends(get_connected_extension_service),
        _: bool = Depends(ensure_user_id)
):
    assistant_result = await assistant_service.create_assistant(
        user_id=user_id,
        request=CreateAssistantRequest(
            name=request.name,
            description=request.description,
            type=request.type,
        )
    )

    if assistant_result.status != 200:
        return ResponseWrapper.wrap(status=assistant_result.status, message=assistant_result.message)

    assistant = assistant_result.data

    workers = []

    if request.type == "mcp":
        for mcp_id in request.worker_ids:
            # Check if mcp_id is valid
            connected_mcp_result = await connected_mcp_service.get_connected_mcp_by_id(user_id, mcp_id)
            if connected_mcp_result.status != 200:
                return ResponseWrapper.wrap(status=connected_mcp_result.status, message=connected_mcp_result.message)

            # Create mcp-assistant
            mcp_result = await mcp_assistant_service.create_mcp_assistant(
                request=CreateMcpAssistantRequest(
                    mcp_id=mcp_id,
                    assistant_id=assistant.id,
                ),
            )

            if mcp_result.status != 200:
                return ResponseWrapper.wrap(status=mcp_result.status, message=mcp_result.message)

            workers.append(
                McpData(
                    id=mcp_id,
                    mcp_name=connected_mcp_result.data.mcp_name,
                    url=connected_mcp_result.data.url,
                    connection_type=connected_mcp_result.data.connection_type,
                    created_at=connected_mcp_result.data.created_at,
                )
            )

    elif request.type == "extension":
        for extension_id in request.worker_ids:
            # Check if extension_id is valid
            connected_extension_result = await connected_extension_service.get_connected_extension_by_id(user_id,
                                                                                                         extension_id)
            if connected_extension_result.status != 200:
                return ResponseWrapper.wrap(status=connected_extension_result.status,
                                            message=connected_extension_result.message)

            # Create extension-assistant
            extension_result = await extension_assistant_service.create_extension_assistant(
                request=CreateExtensionAssistantRequest(
                    assistant_id=assistant.id,
                    extension_id=extension_id,
                ),
            )

            if extension_result.status != 200:
                return ResponseWrapper.wrap(status=extension_result.status, message=extension_result.message)

            workers.append(
                ExtensionData(
                    id=extension_id,
                    extension_name=connected_extension_result.data.extension_name,
                    connected_account_id=connected_extension_result.data.connected_account_id,
                    auth_scheme=connected_extension_result.data.auth_scheme,
                    auth_value=connected_extension_result.data.auth_value,
                    created_at=connected_extension_result.data.created_at,
                )
            )

    data = CreateFullInfoAssistantResponse(
        **assistant.model_dump(),
        workers=workers
    )

    return ResponseWrapper.wrap(status=200, data=data).to_response()


@router.get("/{user_id}/{assistant_id}/get-detail", summary="Get assistant details.",
            response_model=ResponseWrapper[GetFullInfoAssistantResponse])
async def get_full_info_assistant_by_id(
        user_id: str,
        assistant_id: str,
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    assistant_result = await assistant_service.get_assistant_by_id(user_id, assistant_id)

    if assistant_result.status != 200:
        return ResponseWrapper.wrap(status=assistant_result.status, message=assistant_result.message)

    assistant = assistant_result.data

    data = None
    if assistant.type == "mcp":
        mcps_result = await mcp_assistant_service.list_mcps_of_assistant(assistant.id)

        if mcps_result.status != 200:
            return ResponseWrapper.wrap(status=mcps_result.status, message=mcps_result.message)

        mcps = [McpData(
            id=mcp.mcp_id,
            mcp_name=mcp.mcp_name,
            url=mcp.url,
            connection_type=mcp.connection_type,
            created_at=mcp.created_at,
        ) for mcp in mcps_result.data.mcps]

        data = GetFullInfoAssistantResponse(
            **assistant.model_dump(),
            workers=mcps
        )
    elif assistant.type == "extension":
        extensions_result = await extension_assistant_service.list_extensions_of_assistant(assistant.id)

        if extensions_result.status != 200:
            return ResponseWrapper.wrap(status=extensions_result.status, message=extensions_result.message)

        extensions = [ExtensionData(
            id=extension.extension_id,
            extension_name=extension.extension_name,
            connected_account_id=extension.connected_account_id,
            auth_scheme=extension.auth_scheme,
            auth_value=extension.auth_value,
            created_at=extension.created_at,
        ) for extension in extensions_result.data.extensions]

        data = GetFullInfoAssistantResponse(
            **assistant.model_dump(),
            workers=extensions
        )

    return ResponseWrapper.wrap(status=200, data=data).to_response()


@router.patch("/{user_id}/{assistant_id}/update", summary="Update assistant information.",
              response_model=ResponseWrapper[UpdateFullInfoAssistantResponse])
async def update_assistant(
        user_id: str,
        assistant_id: str,
        request: UpdateFullInfoAssistantRequest,
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    assistant_result = await assistant_service.update_assistant(
        user_id=user_id,
        assistant_id=assistant_id,
        assistant=UpdateAssistantRequest(
            **request.model_dump()
        )
    )

    if assistant_result.status != 200:
        return ResponseWrapper.wrap(status=assistant_result.status, message=assistant_result.message)

    assistant = assistant_result.data

    workers = []

    if request.worker_ids is not None:
        if assistant.type == "mcp":
            # Delete all mcps of assistant
            mcps_result = await mcp_assistant_service.delete_all_mcps_of_assistant(assistant.id)
            if mcps_result.status != 200:
                return ResponseWrapper.wrap(status=mcps_result.status, message=mcps_result.message)

            # Create new mcps
            for mcp_id in request.worker_ids:
                mcp_result = await mcp_assistant_service.create_mcp_assistant(
                    request=CreateMcpAssistantRequest(
                        mcp_id=mcp_id,
                        assistant_id=assistant.id,
                    ),
                )

                if mcp_result.status != 200:
                    return ResponseWrapper.wrap(status=mcp_result.status, message=mcp_result.message)

                workers.append(
                    McpData(
                        id=mcp_id,
                        mcp_name=mcp_result.data.mcp_name,
                        url=mcp_result.data.url,
                        connection_type=mcp_result.data.connection_type,
                        created_at=mcp_result.data.created_at,
                    )
                )

        elif assistant.type == "extension":
            # Delete all extensions of assistant
            extensions_result = await extension_assistant_service.delete_all_extensions_of_assistant(assistant.id)
            if extensions_result.status != 200:
                return ResponseWrapper.wrap(status=extensions_result.status, message=extensions_result.message)

            # Create new extensions
            for extension_id in request.worker_ids:
                extension_result = await extension_assistant_service.create_extension_assistant(
                    user_id=user_id,
                    request=CreateExtensionAssistantRequest(
                        assistant_id=assistant.id,
                        extension_id=extension_id,
                    ),
                )

                if extension_result.status != 200:
                    return ResponseWrapper.wrap(status=extension_result.status, message=extension_result.message)

                workers.append(
                    ExtensionData(
                        id=extension_id,
                        extension_name=extension_result.data.extension_name,
                        connected_account_id=extension_result.data.connected_account_id,
                        auth_scheme=extension_result.data.auth_scheme,
                        auth_value=extension_result.data.auth_value,
                        created_at=extension_result.data.created_at,
                    )
                )
    else:
        if assistant.type == "mcp":
            mcps_result = await mcp_assistant_service.list_mcps_of_assistant(assistant.id)
            if mcps_result.status != 200:
                return ResponseWrapper.wrap(status=mcps_result.status, message=mcps_result.message)

            mcps = [McpData(
                id=mcp.mcp_id,
                mcp_name=mcp.mcp_name,
                url=mcp.url,
                connection_type=mcp.connection_type,
                created_at=mcp.created_at,
            ) for mcp in mcps_result.data.mcps]
            workers.extend(mcps)

        if assistant.type == "extension":
            extensions_result = await extension_assistant_service.list_extensions_of_assistant(assistant.id)
            if extensions_result.status != 200:
                return ResponseWrapper.wrap(status=extensions_result.status, message=extensions_result.message)

            extensions = [ExtensionData(
                id=extension.extension_id,
                extension_name=extension.extension_name,
                connected_account_id=extension.connected_account_id,
                auth_scheme=extension.auth_scheme,
                auth_value=extension.auth_value,
                created_at=extension.created_at,
            ) for extension in extensions_result.data.extensions]
            workers.extend(extensions)

    data = UpdateFullInfoAssistantResponse(
        **assistant.model_dump(),
        workers=workers
    )

    return ResponseWrapper.wrap(status=200, data=data).to_response()


@router.delete("/{user_id}/{assistant_id}/delete", summary="Delete a thread.",
               response_model=ResponseWrapper[DeleteThreadResponse])
async def delete_assistant(
        user_id: str,
        assistant_id: str,
        assistant_service: AssistantService = Depends(get_assistant_service),
        extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
        mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
        _: bool = Depends(ensure_user_id),
):
    # Delete all mcps of assistant
    await mcp_assistant_service.delete_all_mcps_of_assistant(assistant_id)

    # Delete all extensions of assistant
    await extension_assistant_service.delete_all_extensions_of_assistant(assistant_id)

    response = await assistant_service.delete_assistant(user_id, assistant_id)
    return response.to_response()

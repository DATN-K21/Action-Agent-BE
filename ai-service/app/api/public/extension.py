from fastapi import APIRouter, Depends

from app.api.deps import ensure_authenticated, ensure_user_id
from app.core import logging
from app.core.cache.cached_agents import AgentCache
from app.core.cache.deps import get_agent_cache
from app.core.graph.deps import get_extension_builder_manager, get_extension
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.schemas.base import ResponseWrapper
from app.schemas.extension import (
    ActiveAccountResponse,
    CheckConnectionResponse,
    GetActionsResponse,
    GetExtensionsResponse,
    GetSocketioInfoResponse, ExtensionRequest, ExtensionResponse, ExtensionCallBack,
)
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.deps import get_connected_app_service
from app.services.extensions.deps import get_extension_service_manager
from app.services.extensions.extension_service_manager import ExtensionServiceManager

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/extension", tags=["Extension"])


@router.get(path="/get-all", summary="Get the list of extensions available.",
            response_model=ResponseWrapper[GetExtensionsResponse])
async def get_extensions(
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        _: bool = Depends(ensure_authenticated),
):
    try:
        extensions = extension_service_manager.get_all_extension_service_names()
        response_data = GetExtensionsResponse(extensions=extensions)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get(path="/{extension_name}/get-actions", summary="Get actions available for extension.",
            response_model=ResponseWrapper[GetActionsResponse])
async def get_actions(
        extension_name: str,
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        _: bool = Depends(ensure_authenticated),
):
    try:
        # 1. Get the extension service
        extension_service = extension_service_manager.get_extension_service(extension_name)
        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        # 2. Get the actions from the extension service
        extension_service.get_actions()
        actions = extension_service.get_action_names()
        response_data = GetActionsResponse(actions=list(actions))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error fetching actions: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post(path="/active", summary="Initialize the connection.",
             response_model=ResponseWrapper[ActiveAccountResponse])
async def active(
        user_id: str,
        extension_name: str,
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the extension service
        extension_service = extension_service_manager.get_extension_service(extension_name)
        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        # 2. Initialize the connection
        connection_request = extension_service.initialize_connection(str(user_id))
        if connection_request is None:
            response_data = ActiveAccountResponse(is_existed=True, redirect_url=None)
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        response_data = ActiveAccountResponse(is_existed=False, redirect_url=connection_request.redirectUrl)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"[extension/active] Error in activating account: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post(path="/disconnect", summary="Disconnect the account.", response_model=ResponseWrapper)
async def disconnect(
        user_id: str,
        extension_name: str,
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the extension service
        extension_service = extension_service_manager.get_extension_service(extension_name)
        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        # 2. Get the account id
        account_id = await connected_app_service.get_account_id(user_id, extension_name)
        if account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()

        # 3. Disconnect the account
        response_data = extension_service.disconnect(account_id)

        # 4. Delete the account from the database
        if response_data.status == "success":
            result = await connected_app_service.delete_connected_app(user_id, extension_name)
            if not result:
                return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get(path="/check-active", summary="Check the connection.",
            response_model=ResponseWrapper[CheckConnectionResponse])
async def check_active(
        user_id: str,
        extension_name: str,
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the extension service
        extension_service = extension_service_manager.get_extension_service(extension_name)
        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        # 2. Check the connection
        result = extension_service.check_connection(str(user_id))

        response_data = CheckConnectionResponse(is_connected=result)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"[extension/check_active] Error in checking connection: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/socketio-info")
async def get_info():
    response_data = GetSocketioInfoResponse(
        output="""
1. General Information
    - URL: http://hostdomain/ 
    - Namespace: /extension
    - Some client listeners: error, connect, disconnect
    - Some server listeners: connect, disconnect, message, set_timezone
    
2. Chat Endpoint:
    - Event name: chat, chat_interrupt
    - Client listens to: chat_response, handle_chat_interrupt
    - Description: This Socket.io endpoint enables agent communication through message-based chatting.

3. Stream Endpoint:
    - Event name: stream, stream_interrupt
    - Client listens to: stream_response, handle_stream_interrupt
    - Description: This Socket.io endpoint facilitates agent communication through message streaming.
"""
    )
    return ResponseWrapper.wrap(status=200, data=response_data).to_response()


@router.post("/chat")
async def chat(
        request: ExtensionRequest = Depends(),
        agent_cache: AgentCache = Depends(get_agent_cache),
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        builder_manager: ExtensionBuilderManager = Depends(get_extension_builder_manager),
):
    try:
        agent = get_extension(
            extension_name=request.extension_name,
            user_id=request.user_id,
            agent_cache=agent_cache,
            extension_service_manager=extension_service_manager,
            builder_manager=builder_manager,
            logger=logger,
        )

        response = await agent.async_chat(
            question=request.input,
            thread_id=request.thread_id,
            max_recursion=request.max_recursion if request.max_recursion is not None else 10,
        )

        return ResponseWrapper.wrap(
            status=200,
            data=ExtensionResponse(
                user_id=request.user_id,
                thread_id=request.thread_id,
                extension_name=request.extension_name,
                interrupted=response.interrupted,
                output=response.output
            )
        ).to_response()

    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/chat-interrupt")
async def chat_interrupt(
        request: ExtensionCallBack = Depends(),
        agent_cache: AgentCache = Depends(get_agent_cache),
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
        builder_manager: ExtensionBuilderManager = Depends(get_extension_builder_manager),
):
    try:
        agent = get_extension(
            extension_name=request.extension_name,
            user_id=request.user_id,
            agent_cache=agent_cache,
            extension_service_manager=extension_service_manager,
            builder_manager=builder_manager,
            logger=logger,
        )

        execute = request.execute
        tool_calls = request.tool_calls
        result = await agent.async_handle_chat_interrupt(
            execute=execute,
            tool_calls=tool_calls,
            thread_id=request.thread_id,
            max_recursion=request.max_recursion if request.max_recursion is not None else 10,
        )

        if execute:
            return ResponseWrapper.wrap(
                status=200,
                data=ExtensionResponse(
                    user_id=request.user_id,
                    thread_id=request.thread_id,
                    extension_name=request.extension_name,
                    interrupted=False,
                    output=result.output
                )
            ).to_response()
        else:
            return ResponseWrapper.wrap(
                status=200,
                data=ExtensionResponse(
                    user_id=request.user_id,
                    thread_id=request.thread_id,
                    extension_name=request.extension_name,
                    interrupted=False,
                    output=""
                )
            ).to_response()
    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/stream")
async def stream(
        request: ExtensionRequest = Depends(),
):
    return ResponseWrapper.wrap(status=200).to_response()


@router.post("/stream-interrupt")
async def stream_interrupt(
        request: ExtensionRequest = Depends(),
):
    return ResponseWrapper.wrap(status=200).to_response()

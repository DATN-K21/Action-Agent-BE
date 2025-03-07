from fastapi import APIRouter, Depends

from app.core import logging
from app.schemas.agent import AgentResponse
from app.schemas.base import ResponseWrapper
from app.schemas.extension import ActiveAccountResponse, GetActionsResponse, GetExtensionsResponse
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.deps import get_connected_app_service
from app.services.extensions.deps import get_extension_service_manager
from app.services.extensions.extension_service_manager import ExtensionServiceManager

logger = logging.get_logger(__name__)

router = APIRouter()


@router.get(
    path="/all",
    tags=["Extension"],
    description="Get the list of extensions available.",
    response_model=ResponseWrapper[GetExtensionsResponse]
)
async def get_extensions(
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager)
):
    try:
        extensions = extension_service_manager.get_all_extension_service_names()
        response_data = GetExtensionsResponse(extensions=list(extensions))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[extension/get_extensions] Error fetching extensions: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get(
    path="/{extension_name}/actions",
    tags=["Extension"],
    description="Get the list of actions available for the extension.",
    response_model=ResponseWrapper[GetActionsResponse]
)
async def get_actions(
        extension_name: str,
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager)
):
    try:
        extension_service = extension_service_manager.get_extension_service(extension_name)

        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        extension_service.get_actions()

        actions = extension_service.get_action_names()
        response_data = GetActionsResponse(actions=list(actions))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[gmail_agent/get_actions] Error fetching actions: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post(
    path="/active",
    tags=["Extension"],
    description="Initialize the connection.",
    response_model=ResponseWrapper[ActiveAccountResponse]
)
async def active(
        user_id: str,
        extension_name: str,
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
):
    try:
        extension_service = extension_service_manager.get_extension_service(extension_name)

        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        connection_request = extension_service.initialize_connection(str(user_id))

        if connection_request is None:
            response_data = ActiveAccountResponse(is_existed=True, redirect_url=None)
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        response_data = ActiveAccountResponse(is_existed=False, redirect_url=connection_request.redirectUrl)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"[extension/active] Error in activating account: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post(
    path="/disconnect",
    tags=["Extension"],
    description="Disconnect the account.",
    response_model=ResponseWrapper
)
async def logout(
        user_id: str,
        extension_name: str,
        connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
        extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager)
):
    try:
        extension_service = extension_service_manager.get_extension_service(extension_name)

        if extension_service is None:
            return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()

        account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()
        response_data = extension_service.logout(account_id)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[extension/logout] Error in logging out: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/ws-info")
async def get_info():
    return ResponseWrapper.wrap(
        status=200,
        data=AgentResponse(
            output="""
1. Chat Endpoint:
    URL: http://hostdomain/extension/ws/chat/{user_id}/{thread_id}/{extension_name}/{max_recursion}
    Description: This WebSocket endpoint enables agent communication through message-based chatting.

2. Stream Endpoint:
   URL: http://dostdomain/extension/ws/stream/{user_id}/{thread_id}/{extension_name}/{max_recursion}
   Description: This WebSocket endpoint facilitates agent communication through message streaming.
"""
        ),  # type: ignore
    ).to_response()  # type: ignore

# noinspection DuplicatedCode
# @router.websocket("/ws/chat/{user_id}/{thread_id}/{extension_name}/{max_recursion}")
# async def execute(
#         websocket: WebSocket,
#         user_id: str,
#         thread_id: str,
#         extension_name: str,
#         max_recursion: Optional[int] = 5,
#         builder_manager: ExtensionBuilderManager = Depends(get_extension_builder_manager),
#         extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
# ):
#     is_connected = False
#
#     try:
#         extension_service = extension_service_manager.get_extension_service(extension_name)
#         builder_manager.update_builder_tools(
#             builder_name=extension_name,
#             tools=extension_service.get_authed_tools(user_id),  # type: ignore
#         )
#
#         builder = builder_manager.get_extension_builder(extension_name)
#
#         if builder is None:
#             return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()
#
#         graph = builder.build_graph(perform_action=True, has_human_acceptance_flow=True)
#         agent = Agent(graph)
#
#         await websocket.accept()
#         logger.info("[Opened websocket connection]")
#
#         is_connected = True
#
#         user_input = await websocket.receive_text()
#
#         response = await agent.async_chat(
#             question=user_input,
#             thread_id=thread_id,
#             max_recursion=max_recursion if max_recursion is not None else 5,
#         )
#
#         # TODO: Create schema for response
#         await websocket.send_json(
#             {
#                 "threadID": thread_id,
#                 "interrupted": response.interrupted,
#                 "output": response.output,
#             }
#         )
#
#         if response.interrupted:
#             data = await websocket.receive_text()
#             if data == "continue":
#                 action = HumanAction.CONTINUE
#                 result = await agent.async_handle_chat_interrupt(
#                     action=action,
#                     thread_id=thread_id,
#                     max_recursion=max_recursion if max_recursion is not None else 5,
#                 )
#
#                 # TODO: Create schema for response
#                 await websocket.send_json(
#                     {
#                         "threadID": thread_id,
#                         "output": result.output,
#                     }
#                 )
#
#             return ResponseWrapper.wrap(status=200, data=AgentResponse(
#                 thread_id=thread_id,
#                 output="Successfull",
#             )).to_response()
#
#     except WebSocketDisconnect:
#         logger.info("[WebSocketDisconnect] websocket disconnected")
#         is_connected = False
#         return ResponseWrapper.wrap(status=200, data=AgentResponse(
#             thread_id=thread_id,
#             output="Successfull",
#         )
#                                     ).to_response()
#
#     except Exception as e:
#         logger.error(f"Error in executing Gmail API: {str(e)}", exc_info=True)
#         return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
#
#     finally:
#         if is_connected:
#             await websocket.close()
#             logger.info("[Close socket manually] Closed websocket connection")
#
#
# # noinspection DuplicatedCode
# @router.websocket("/ws/stream/{user_id}/{thread_id}/{extension_name}/{max_recursion}")
# async def stream(
#         websocket: WebSocket,
#         user_id: str,
#         thread_id: str,
#         extension_name: str,
#         max_recursion: Optional[int] = 5,
#         builder_manager: ExtensionBuilderManager = Depends(get_extension_builder_manager),
#         extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
# ):
#     is_connected = False
#
#     try:
#         extension_service = extension_service_manager.get_extension_service(extension_name)
#         builder_manager.update_builder_tools(
#             builder_name=extension_name,
#             tools=extension_service.get_authed_tools(user_id),  # type: ignore
#         )
#
#         builder = builder_manager.get_extension_builder(extension_name)
#
#         if builder is None:
#             return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()
#
#         graph = builder.build_graph(perform_action=True, has_human_acceptance_flow=True)
#         agent = Agent(graph)
#
#         await websocket.accept()
#         logger.info("[Opened websocket connection]")
#
#         is_connected = True
#
#         user_input = await websocket.receive_text()
#         response = await agent.async_stream(
#             question=user_input,
#             thread_id=thread_id,
#             max_recursion=max_recursion if max_recursion is not None else 5,
#         )
#
#         async for dict_message in to_sse(response):
#             await websocket.send_json(dict_message)
#
#         data = await websocket.receive_text()
#         if data == "continue":
#
#             action = HumanAction.CONTINUE
#
#             result = await agent.async_handle_stream_interrupt(
#                 action=action,
#                 thread_id=thread_id,
#                 max_recursion=max_recursion if max_recursion is not None else 5,
#             )
#
#             async for dict_message in to_sse(result):
#                 await websocket.send_json(dict_message)
#
#         return ResponseWrapper.wrap(status=200, data=AgentResponse(
#             thread_id=thread_id,
#             output="Successfull",
#         )
#                                     ).to_response()
#
#     except WebSocketDisconnect:
#         logger.info("[WebSocketDisconnect] websocket disconnected")
#         is_connected = False
#         return ResponseWrapper.wrap(status=200, data=AgentResponse(
#             thread_id=thread_id,
#             output="Successfull",
#         )
#                                     ).to_response()
#
#     except Exception as e:
#         logger.error(f"Error executing Gmail API: {str(e)}", exc_info=True)
#         return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
#
#     finally:
#         if is_connected:
#             await websocket.close()
#             logger.info("[Close socket manually] Closed websocket connection")

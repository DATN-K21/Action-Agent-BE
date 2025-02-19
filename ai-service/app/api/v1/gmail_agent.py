from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core import logging
from app.dependencies import get_connected_app_service, get_gmail_service, get_identity_service
from app.schemas.base import ResponseWrapper
from app.schemas.connection import ActiveAccountResponse, GetActionsResponse
from app.services.database.connected_app_service import ConnectedAppService
from app.services.extensions.gmail_service import GmailService
from app.services.identity_service import IdentityService
from app.utils.enums import HumanAction
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/active", description="Handle successful Gmail connection.", response_model=ResponseWrapper[ActiveAccountResponse])
async def active(
    user_id: str,
    gmail_service: GmailService = Depends(get_gmail_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    try:
        connection_request = gmail_service.initialize_connection(str(user_id))

        if connection_request is None:
            response_data = ActiveAccountResponse(isExisted=False, redirectUrl=None)
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        response_data = ActiveAccountResponse(isExisted=True, redirectUrl=connection_request.redirectUrl)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"[gmail_agent/active] Error in activating account: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/logout", tags=["Gmail"], description="Handle Gmail logout.")
async def logout(
    user_id: str,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
    gmail_service: GmailService = Depends(get_gmail_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    try:
        account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()
        response_data = await gmail_service.logout(account_id)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[gmail_agent/logout] Error in logging out: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/actions")
async def get_actions():
    try:
        actions = GmailService.get_actions()
        response_data = GetActionsResponse(actions=actions)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[gmail_agent/get_actions] Error fetching actions: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.websocket("/ws/chat/{user_id}/{thread_id}/{max_recursion}")
async def execute_gmail(
    websocket: WebSocket,
    user_id: str,
    thread_id: str,
    max_recursion: Optional[int] = 5,
    gmail_service: GmailService = Depends(get_gmail_service),
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    try:
        logger.info("[Opened websocket connection]")
        await websocket.accept()
        is_connected = True

        connected_account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if connected_account_id is None:
            return

        tools = gmail_service.get_authed_tools(user_id, connected_account_id)
        user_input = await websocket.receive_text()

        response = await gmail_service.execute_gmail(
            user_input=user_input,
            thread_id=thread_id,
            tools=tools,
            max_recursion=max_recursion if max_recursion is not None else 5,
        )

        await websocket.send_json(
            {
                "threadID": thread_id,
                "interrupted": response["interrupted"],
                "output": response["output"],
            }
        )

        if response["interrupted"]:
            data = await websocket.receive_text()
            if data != "continue":
                return

            action = HumanAction.CONTINUE
            result = await gmail_service.handle_interrupt_execute_gmail(
                action=action,
                thread_id=thread_id,
                tools=tools,
                max_recursion=max_recursion if max_recursion is not None else 5,
            )

            await websocket.send_json(
                {
                    "threadID": thread_id,
                    "output": result,
                }
            )

    except WebSocketDisconnect:
        logger.info("[WebSocketDisconnect] websocket disconnected")
        is_connected = False

    except Exception as e:
        logger.error("Error executing Gmail API: %s", str(e))

    finally:
        if is_connected:
            await websocket.close()
            logger.info("[Close socket manually] Closed websocket connection")


@router.websocket("/ws/stream/{user_id}/{thread_id}/{max_recursion}")
async def stream_gmail(
    websocket: WebSocket,
    user_id: str,
    thread_id: str,
    max_recursion: Optional[int] = 5,
    gmail_service: GmailService = Depends(get_gmail_service),
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    try:
        logger.info("[Opened websocket connection]")
        await websocket.accept()
        is_connected = True

        connected_account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if connected_account_id is None:
            return

        tools = gmail_service.get_authed_tools(user_id, connected_account_id)

        user_input = await websocket.receive_text()
        response = await gmail_service.stream_gmail(
            user_input=user_input,
            thread_id=thread_id,
            tools=tools,
            max_recursion=max_recursion if max_recursion is not None else 5,
        )

        async for dict_message in to_sse(response):
            await websocket.send_json(dict_message)

        data = await websocket.receive_text()
        if data != "continue":
            return

        action = HumanAction.CONTINUE

        result = await GmailService.handle_interrupt_stream_gmail(
            action=action,
            thread_id=thread_id,
            tools=tools,
            max_recursion=max_recursion if max_recursion is not None else 5,
        )

        async for dict_message in to_sse(result):
            await websocket.send_json(dict_message)

    except WebSocketDisconnect:
        logger.info("[WebSocketDisconnect] websocket disconnected")
        is_connected = False

    except Exception as e:
        logger.error("Error executing Gmail API: %s", str(e))

    finally:
        if is_connected:
            await websocket.close()
            logger.info("[Close socket manually] Closed websocket connection")

from typing import Optional, Literal

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core import logging
from app.core.agents.deps import get_chat_agent, get_search_agent, get_rag_agent, get_gmail_agent
from app.memory.deps import get_checkpointer
from app.schemas.base import ResponseWrapper
from app.schemas.chat import AgentResponse
from app.schemas.connection import GetActionsResponse
from app.services.database.connected_app_service import ConnectedAppService
from app.services.deps import get_connected_app_service
from app.services.extensions.gmail_service import GmailService
from app.utils.enums import HumanAction
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()

def get_agent(agent_name: str):
    if agent_name == "chat_agent":
        return get_chat_agent()
    elif agent_name == "search_agent":
        return get_search_agent()
    elif agent_name == "rag_agent":
        return get_rag_agent()
    elif agent_name == "gmail_agent":
        return None


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
async def execute(
    websocket: WebSocket,
    user_id: str,
    thread_id: str,
    max_recursion: Optional[int] = 5,
    agent_name: Optional[str] = None,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    is_connected = False

    try:
        agent_name = "chat_agent" if agent_name is None else agent_name
        agent = get_agent(agent_name)

        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        await websocket.accept()
        logger.info("[Opened websocket connection]")

        is_connected = True

        connected_account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if connected_account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()

        user_input = await websocket.receive_text()

        response = await agent.async_execute(
            question=user_input,
            thread_id=thread_id,
            user_id=user_id,
            connected_account_id=connected_account_id,
            max_recursion=max_recursion if max_recursion is not None else 5,
        )

        #TODO: Create schema for response
        await websocket.send_json(
            {
                "threadID": thread_id,
                "interrupted": response.interrupted,
                "output": response.output,
            }
        )

        if response.interrupted:
            data = await websocket.receive_text()
            if data == "continue":
                action = HumanAction.CONTINUE
                result = await agent.async_handle_execution_interrupt(
                    action=action,
                    thread_id=thread_id,
                    user_id=user_id,
                    connected_account_id=connected_account_id,
                    max_recursion=max_recursion if max_recursion is not None else 5,
                )

                # TODO: Create schema for response
                await websocket.send_json(
                    {
                        "threadID": thread_id,
                        "output": result.output,
                    }
                )

            return ResponseWrapper.wrap(status=200, data=AgentResponse(
                success=True,
                thread_id=thread_id,
                output="Successfull",
            )).to_response()

    except WebSocketDisconnect:
        logger.info("[WebSocketDisconnect] websocket disconnected")
        is_connected = False
        return ResponseWrapper.wrap(status=200, data=AgentResponse(
                success=True,
                thread_id=thread_id,
                output="Successfull",
            )
        ).to_response()

    except Exception as e:
        logger.error("Error in executing Gmail API: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

    finally:
        if is_connected:
            await websocket.close()
            logger.info("[Close socket manually] Closed websocket connection")


@router.websocket("/ws/stream/{user_id}/{thread_id}/{max_recursion}")
async def stream(
    websocket: WebSocket,
    user_id: str,
    thread_id: str,
    max_recursion: Optional[int] = 5,
    agent_name: Optional[str] = None,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    is_connected = False

    try:
        agent_name = "chat_agent" if agent_name is None else agent_name
        agent = get_agent(agent_name)
        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        await websocket.accept()
        logger.info("[Opened websocket connection]")

        is_connected = True

        connected_account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if connected_account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()


        user_input = await websocket.receive_text()
        response = await agent.async_stream(
            question=user_input,
            thread_id=thread_id,
            user_id=user_id,
            connected_account_id=connected_account_id,
            max_recursion=max_recursion if max_recursion is not None else 5,
        )

        async for dict_message in to_sse(response):
            await websocket.send_json(dict_message)

        data = await websocket.receive_text()
        if data == "continue":

            action = HumanAction.CONTINUE

            result = await agent.async_handle_interrupt_stream(
                action=action,
                thread_id=thread_id,
                user_id=user_id,
                connected_account_id=connected_account_id,
                max_recursion=max_recursion if max_recursion is not None else 5,
            )

            async for dict_message in to_sse(result):
                await websocket.send_json(dict_message)

        return ResponseWrapper.wrap(status=200, data=AgentResponse(
                success=True,
                thread_id=thread_id,
                output="Successfull",
            )
        ).to_response()

    except WebSocketDisconnect:
        logger.info("[WebSocketDisconnect] websocket disconnected")
        is_connected = False
        return ResponseWrapper.wrap(status=200, data=AgentResponse(
                success=True,
                thread_id=thread_id,
                output="Successfull",
            )
        ).to_response()

    except Exception as e:
        logger.error("Error executing Gmail API: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

    finally:
        if is_connected:
            await websocket.close()
            logger.info("[Close socket manually] Closed websocket connection")
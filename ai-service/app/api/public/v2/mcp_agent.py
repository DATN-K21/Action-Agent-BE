from fastapi import APIRouter, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse
from starlette.responses import StreamingResponse

from app.api.auth import ensure_user_id
from app.core import logging
from app.core.cache.cached_mcp_agents import McpAgentCache, get_mcp_agent_cache
from app.core.graph.v2.mcp_agent import create_mcp_agent_no_cache
from app.core.session import get_db_session
from app.core.utils.config_helper import create_invocation_config
from app.core.utils.streaming import astream_state, to_sse
from app.memory.checkpoint import get_checkpointer
from app.models import Thread
from app.schemas.base import ResponseWrapper
from app.schemas.mcp_agent import McpResponse, McpRequest, GetMcpActionsResponse
from app.services.database.connected_mcp_service import ConnectedMcpService, get_connected_mcp_service
from app.services.mcps.mcp_service import aget_all_mcp_actions, aget_mcp_actions_in_a_server

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/mcp-agent", tags=["API-V2 | MCP Agent"])


@router.get(path="/{user_id}/get-actions", summary="Get available actions for mcps.",
            response_model=ResponseWrapper[GetMcpActionsResponse])
async def get_all_actions(
        user_id: str,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    try:
        result = await aget_all_mcp_actions(user_id, connected_mcp_service)

        return ResponseWrapper.wrap(
            status=200,
            data=GetMcpActionsResponse(
                actions=result
            )
        ).to_response()


    except Exception as e:
        logger.error(f"Error fetching actions: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get(path="/{user_id}/{connected_mcp_id}/get-actions", summary="Get available actions for a mcp.",
            response_model=ResponseWrapper[GetMcpActionsResponse])
async def get_all_actions_in_a_server(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        _: bool = Depends(ensure_user_id),
):
    try:
        result = await aget_mcp_actions_in_a_server(user_id, connected_mcp_id, connected_mcp_service)

        return ResponseWrapper.wrap(
            status=200,
            data=GetMcpActionsResponse(
                actions=result
            )
        ).to_response()

    except Exception as e:
        logger.error(f"Error fetching actions: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/chat/{user_id}/{thread_id}", summary="Chat with the mcp agent.",
             response_model=ResponseWrapper[McpResponse])
async def chat(
        user_id: str,
        thread_id: str,
        request: McpRequest,
        mcp_agent_cache: McpAgentCache = Depends(get_mcp_agent_cache),
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
):
    try:
        # Check the thread
        stmt = (
            select(Thread.id)
            .where(
                Thread.user_id == user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )
        db_thread = (await db.execute(stmt)).scalar_one_or_none()
        if db_thread is None:
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        config = create_invocation_config(
            thread_id=thread_id,
            recursion_limit=request.recursion_limit,
        )
        async with create_mcp_agent_no_cache(
                user_id=user_id,
                connected_mcp_service=connected_mcp_service,
                checkpointer=checkpointer
        ) as agent:
            response = await agent.ainvoke(
                input={"messages": [request.input]},
                config=config
            )

            return ResponseWrapper.wrap(
                status=200,
                data=McpResponse(
                    user_id=user_id,
                    thread_id=thread_id,
                    output=response["messages"][-1].content
                )
            ).to_response()

    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/stream/{user_id}/{thread_id}", summary="Stream the mcp agent.",
             response_class=StreamingResponse)
async def stream(
        user_id: str,
        thread_id: str,
        request: McpRequest,
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id)
):
    # Check the thread
    stmt = (
        select(Thread.id)
        .where(
            Thread.user_id == user_id,
            Thread.id == thread_id,
            Thread.is_deleted.is_(False),
        )
        .limit(1)
    )
    db_thread = (await db.execute(stmt)).scalar_one_or_none()
    if db_thread is None:
        return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

    config = create_invocation_config(
        thread_id=thread_id,
        recursion_limit=request.recursion_limit,
    )

    async with create_mcp_agent_no_cache(
            user_id=user_id,
            connected_mcp_service=connected_mcp_service,
            checkpointer=checkpointer
    ) as agent:
        response = astream_state(app=agent, input_={"messages": [request.input]}, config=config,
                                 allow_stream_nodes=None)

        return EventSourceResponse(to_sse(response))

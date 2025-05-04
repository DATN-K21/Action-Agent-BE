from fastapi import APIRouter, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse
from starlette.responses import StreamingResponse

from app.api.auth import ensure_user_id
from app.core import logging
from app.core.graph.v2_1.base_v2_1 import HumanEditingDataV2
from app.core.graph.v2_1.mcp_agent_v2_1 import create_mcp_agent_no_cache_v2
from app.core.session import get_db_session
from app.core.utils.config_helper import create_invocation_config
from app.core.utils.streaming import astream_state, to_sse
from app.memory.checkpoint import get_checkpointer
from app.models import Thread
from app.schemas.base import ResponseWrapper
from app.schemas.extension import HTTPExtensionCallbackRequest
from app.schemas.mcp_agent import McpResponse, McpRequest
from app.services.database.connected_mcp_service import ConnectedMcpService, get_connected_mcp_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/mcp-agent", tags=["API-V2.1 | MCP Agent"])


@router.post("/chat/{user_id}/{thread_id}", summary="Chat with the mcp agent.",
             response_model=ResponseWrapper[McpResponse])
async def chat(
        user_id: str,
        thread_id: str,
        request: McpRequest,
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
            recursion_limit=request.max_recursion,
        )
        async with create_mcp_agent_no_cache_v2(
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


@router.post("/handle-chat-interrupt/{user_id}/{thread_id}", summary="Handle chat interrupt with the mcp agent.",
             response_model=ResponseWrapper[McpResponse])
async def handle_chat_interrupt(
        user_id: str,
        thread_id: str,
        request: HTTPExtensionCallbackRequest,
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
            recursion_limit=request.max_recursion,
        )
        async with create_mcp_agent_no_cache_v2(
                user_id=user_id,
                connected_mcp_service=connected_mcp_service,
                checkpointer=checkpointer
        ) as agent:
            response = await agent.ainvoke(
                Command(
                    resume=HumanEditingDataV2(
                        execute=request.execute,
                        tool_calls=request.tool_calls
                    ).model_dump()
                ),
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
        recursion_limit=request.max_recursion,
    )

    async with create_mcp_agent_no_cache_v2(
            user_id=user_id,
            connected_mcp_service=connected_mcp_service,
            checkpointer=checkpointer
    ) as agent:
        response = astream_state(app=agent, input_={"messages": [request.input]}, config=config,
                                 allow_stream_nodes=None)

        return EventSourceResponse(to_sse(response))

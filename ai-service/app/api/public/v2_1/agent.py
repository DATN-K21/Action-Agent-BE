from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from app.api.auth import ensure_user_id
from app.core import logging
from app.core.graph.v2_1.base_v2_1 import get_builtin_agent
from app.core.session import get_db_session
from app.core.utils.config_helper import create_invocation_config
from app.core.utils.streaming import to_sse, astream_state
from app.memory.checkpoint import get_checkpointer
from app.models.thread import Thread
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["API-V2.1 | Agent"])


@router.post("/chat/{user_id}/{thread_id}/{agent_name}", summary="Chat with the agent.",
             response_model=ResponseWrapper[AgentChatResponse])
async def execute(
        user_id: str,
        thread_id: str,
        agent_name: str,
        request: AgentChatRequest,
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
):
    try:
        # Get the agent
        agent = get_builtin_agent(agent_name, checkpointer)

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

        # Chat with the agent
        config = create_invocation_config(thread_id, request.recursion_limit)
        response = await agent.ainvoke(input={"messages": [request.input]}, config=config)

        return ResponseWrapper.wrap(
            status=200,
            data=AgentChatResponse(
                thread_id=thread_id,
                output=response["messages"][-1].content,  # type: ignore
            ),
        ).to_response()

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/stream/{user_id}/{thread_id}/{agent_name}", summary="Stream with the agent.",
             response_class=StreamingResponse)
async def stream(
        user_id: str,
        thread_id: str,
        agent_name: str,
        request: AgentChatRequest,
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
):
    try:
        # Get the agent
        agent = get_builtin_agent(agent_name, checkpointer)

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

        config = create_invocation_config(thread_id=thread_id)
        # Chat with the agent
        response = astream_state(app=agent, input_={"messages": [request.input]}, config=config,
                                 allow_stream_nodes=None)

        return EventSourceResponse(to_sse(response))

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

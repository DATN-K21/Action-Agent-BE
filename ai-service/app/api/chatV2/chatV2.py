from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from app.api.deps import ensure_user_id
from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.session import get_db_session
from app.core.utils.streaming import to_sse
from app.models.thread import Thread
from app.schemas.base import ResponseWrapper
from app.schemas.chatV2 import AgentChatV2Request

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/{user_id}/{thread_id}/chat-agent/{agent_name}", summary="Chat with the agent.", response_class=StreamingResponse)
async def chat_agent(
    user_id: str,
    thread_id: str,
    agent_name: str,
    request: AgentChatV2Request,
    agent_manager: AgentManager = Depends(get_agent_manager),
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the agent
        agent = agent_manager.get_agent(name=agent_name)
        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        # 2. Check the thread
        stmt = (
            select(
                Thread.id.label("id"),
                Thread.user_id.label("user_id"),
                Thread.title.label("title"),
                Thread.created_at.label("created_at"),
            )
            .where(
                Thread.user_id == user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await db.execute(stmt)
        db_thread = result.mappings().first()
        if db_thread is None:
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        # 3. Chat with the agent
        response = await agent.async_stream(
            question=request.input,
            thread_id=thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

        return EventSourceResponse(to_sse(response))

    except Exception as e:
        logger.error(f"Error executing API: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

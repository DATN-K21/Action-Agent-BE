from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from app.api.auth import ensure_user_id
from app.core import logging
from app.core.session import get_db_session
from app.core.utils.streaming import to_sse
from app.models.thread import Thread
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.base import ResponseWrapper
from app.services.multi_agent.core.multi_agent_service import MultiAgentService
from app.services.multi_agent.deps import get_multi_agent_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/multi-agent-experimental", tags=["Multi agent experimental"])


@router.post("/chat/{user_id}/{thread_id}", summary="Chat with a complex multi-agent system.",
             response_model=ResponseWrapper[AgentChatResponse])
async def chat(
        user_id: str,
        thread_id: str,
        request: AgentChatRequest,
        multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
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

    response = await multi_agent_service.execute_multi_agent(thread_id, request.input)
    return response.to_response()


@router.post("/stream/{user_id}/{thread_id}", summary="Stream chat with a complex multi-agent system.",
             response_class=EventSourceResponse)
async def stream(
        user_id: str,
        thread_id: str,
        request: AgentChatRequest,
        multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
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

    # Stream chat with the multi-agent system
    response = await multi_agent_service.stream_multi_agent(thread_id, request.input)
    return EventSourceResponse(to_sse(response))

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from app.api.deps import ensure_authenticated, ensure_user_id
from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.session import get_db_session
from app.core.utils.streaming import to_sse
from app.models.thread import Thread
from app.schemas.agent import AgentChatRequest, AgentChatResponse, GetAgentsResponse
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.get("/get-all", summary="Get all agent names.", response_model=ResponseWrapper[GetAgentsResponse])
async def get_agents(
    agent_manager: AgentManager = Depends(get_agent_manager),
    _: bool = Depends(ensure_authenticated),
):
    try:
        agents = agent_manager.get_all_agent_names()
        response_data = GetAgentsResponse(agent_names=list(agents))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/{user_id}/{thread_id}/{agent_name}/chat", summary="Chat with the agent.", response_model=ResponseWrapper[AgentChatResponse])
async def execute(
    user_id: str,
    thread_id: str,
    agent_name: str,
    request: AgentChatRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the agent
        agent = agent_manager.get_agent(agent_name)
        if agent is None:
            logger.warning(f"Agent {agent_name} not found.")
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        # 2. Check the thread
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
            logger.warning(f"Thread {thread_id} not found for user {user_id}.")
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        # 3. Chat with the agent
        response = await agent.async_chat(
            question=request.input,
            thread_id=thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit else 5,
        )

        logger.info(f"Agent {agent_name} response: {response.output}")

        return ResponseWrapper.wrap(
            status=200,
            data=AgentChatResponse(
                thread_id=thread_id,
                output=response.output,  # type: ignore
            ),
        ).to_response()

    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/{user_id}/{thread_id}/{agent_name}/stream", summary="Stream with the agent.", response_class=StreamingResponse)
async def stream(
    user_id: str,
    thread_id: str,
    agent_name: str,
    request: AgentChatRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_user_id),
):
    try:
        # 1. Get the agent
        agent = agent_manager.get_agent(agent_name)
        if agent is None:
            logger.warning(f"Agent {agent_name} not found.")
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        # 2. Check the thread
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
            logger.warning(f"Thread {thread_id} not found for user {user_id}.")
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        # 3. Chat with the agent
        response = await agent.async_stream(
            question=request.input,
            thread_id=thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

        return EventSourceResponse(to_sse(response))

    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

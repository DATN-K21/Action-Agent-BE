from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from app.api.auth import ensure_authenticated, ensure_user_id
from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.session import get_db_session
from app.core.utils.streaming import to_sse
from app.models.agent import BuiltinAgent, CustomAgent
from app.schemas.agent import AgentChatRequest, AgentChatResponse, GetAgentV2ListResponse
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/agent-v2", tags=["Agent-V2"])


@router.get("/get-all", summary="Get all agents.", response_model=ResponseWrapper[GetAgentV2ListResponse])
async def get_agents(
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_authenticated),
):
    """
    Get all agents.
    """
    try:
        # Get all agents
        stmt = select(
            BuiltinAgent.name,
            BuiltinAgent.description,
            BuiltinAgent.image_url,
            BuiltinAgent.tools,
            BuiltinAgent.is_public,
            CustomAgent.child_agents,
        ).where(            BuiltinAgent.is_deleted.is_(False),
                BuiltinAgent.is_public.is_(True))
        builtin_agents = (await db.execute(stmt)).all()
        stmt = select(
            CustomAgent.name,
            CustomAgent.description,
            CustomAgent.image_url,
            CustomAgent.tools,
        ).where(CustomAgent.is_deleted.is_(False))
        custom_agents = (await db.execute(stmt)).all()
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/{agent_name}/chat/{user_id}/{thread_id}", summary="Chat with the agent.", response_model=ResponseWrapper[AgentChatResponse])
async def chat(
    user_id: str,
    thread_id: str,
    agent_name: str,
    request: AgentChatRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_user_id),
):
    try:
        # Get the agent
        agent = agent_manager.get_agent(agent_name)
        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

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
        response = await agent.async_chat(
            question=request.input,
            thread_id=thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

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


@router.post("/stream/{user_id}/{thread_id}/{agent_name}", summary="Stream with the agent.", response_class=StreamingResponse)
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

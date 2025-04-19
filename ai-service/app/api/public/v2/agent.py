from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import ensure_authenticated, ensure_user_id
from app.core import logging
from app.core.graph.v2.baseV2 import AgentMngr, get_agent_managerV2
from app.core.session import get_db_session
from app.models.agent import BuiltinAgent, CustomAgent
from app.models.thread import Thread
from app.schemas._base import ResponseWrapper
from app.schemas.agent import AgentChatRequest, GetAgentV2ListResponse, GetAgentV2Response

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["API-V2"])


@router.get("/get-all", summary="Get all agents.", response_model=ResponseWrapper[GetAgentV2ListResponse])
async def get_agents(
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_authenticated),
):
    """
    Get all agents.
    """
    try:
        # Get builtin agents
        stmt = (
            select(
                BuiltinAgent.name.label("name"),
                BuiltinAgent.description.label("description"),
                BuiltinAgent.image_url.label("image_url"),
                BuiltinAgent.tools.label("tools"),
                BuiltinAgent.is_public.label("is_public"),
                CustomAgent.child_agents.label("child_agents"),
            )
            .where(BuiltinAgent.is_deleted.is_(False), BuiltinAgent.is_public.is_(True))
            .order_by(BuiltinAgent.name)
        )
        builtin_agents = (await db.execute(stmt)).mappings().all()

        # Get custom agents
        stmt = (
            select(
                CustomAgent.name.label("name"),
                CustomAgent.description.label("description"),
                CustomAgent.image_url.label("image_url"),
                CustomAgent.tools.label("tools"),
                CustomAgent.child_agents.label("child_agents"),
            )
            .where(CustomAgent.is_deleted.is_(False))
            .order_by(CustomAgent.name)
        )
        custom_agents = (await db.execute(stmt)).mappings().all()

        # Combine agents
        agents = [GetAgentV2Response.model_validate(agent) for agent in (*builtin_agents, *custom_agents)]
        return ResponseWrapper.wrap(
            status=200,
            data=GetAgentV2ListResponse(agents=agents),
        ).to_response()

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


# Assuming you have this function already
def db_add_message(timestamp: str, role: str, content: str):
    # Your sync DB logic goes here
    print(f"[DB] Inserted: {timestamp} | {role} | {content}")


# ThreadPool executor for running blocking DB logic
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/{agent_name}/stream/{user_id}/{thread_id}/", summary="Stream with the agent.", response_class=StreamingResponse)
async def stream(
    agent_name: str,
    user_id: str,
    thread_id: str,
    request: AgentChatRequest,
    agent_manager: AgentMngr = Depends(get_agent_managerV2),
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(ensure_user_id),
):
    try:
        # Check the thread
        stmt = (
            select(Thread.id.label("id"))
            .where(
                Thread.user_id == user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )
        db_thread = (await db.execute(stmt)).mappings().first()
        if db_thread is None:
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        # Get the agent
        agent = agent_manager.get_agent(agent_name)
        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        # Chat with the agent
        config = RunnableConfig(configurable={"thread_id": thread_id})
        input = {"messages": HumanMessage(content=request.input)}
        async for step in agent.astream(
            input=input,
            config=config,
            stream_mode=["messages", "debug"],
        ):
            if not isinstance(step, tuple):
                continue
            tag, payload = step

            # 1. Handle streamed token-by-token output from LLM
            if tag == "messages":
                message_chunk, metadata = payload
                if isinstance(message_chunk, AIMessageChunk):
                    token = message_chunk.content
                    print(token, end="", flush=True)  # Stream token
                    # Optional: You can gather tokens here to assemble full content

            # 2. Handle 'debug' checkpoint - save to DB in background
            elif tag == "debug":
                if payload.get("type") == "checkpoint":
                    next = payload.get("next")
                    if next == "__start__":
                        continue

                    timestamp = payload.get("timestamp")
                    payload2 = payload.get("payload", {})

                    messages = payload2.get("values", {}).get("messages", [])
                    role = "unknown"
                    content = ""
                    if messages:
                        last_msg = messages[-1]
                        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
                        role = "ai" if isinstance(last_msg, AIMessage) else "human" if isinstance(last_msg, HumanMessage) else "unknown"

                    # # Run DB insert in background to avoid blocking
                    # asyncio.create_task(asyncio.get_event_loop().run_in_executor(executor, db_add_message, timestamp, role, content))
                    print(f"[DB] Inserted: {timestamp} | {role} | {content}")

            print("-", end="", flush=True)  # Stream debug info

        # Finalize the response by summarizing to trim context
        # TODO

        return ResponseWrapper.wrap(status=200).to_response()

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

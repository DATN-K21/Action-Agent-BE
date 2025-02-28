from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.memory.deps import get_checkpointer
from app.services.multi_agent.core.multi_agent_service import MultiAgentService


def get_multi_agent_service(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    return MultiAgentService(checkpointer)
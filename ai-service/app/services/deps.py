
from fastapi import Depends, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.memory.deps import get_checkpointer
from app.services.identity_service import IdentityService
from app.services.multi_agent.core.multi_agent_service import MultiAgentService


# Identity Dependencies
def get_identity_service(request: Request):
    return IdentityService(request)
from fastapi import APIRouter, Depends

from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.utils.converts_messages_to_dict import converts_messages_to_dicts
from app.schemas.base import ResponseWrapper
from app.schemas.history import GetHistoryResponse
from app.schemas.ingest import IngestResponse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.get("/state", tags=["History"], description="", response_model=ResponseWrapper[IngestResponse])
async def get_state(
    threadId: str,
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    try:
        agent = agent_manager.get_agent(name="chat-agent")
        state = await agent.async_get_state(threadId)  # type: ignore

        if "messages" in state.values:
            response_data = converts_messages_to_dicts(state.values["messages"])
            return ResponseWrapper.wrap(status=200, data=GetHistoryResponse(messages=list(response_data))).to_response()
    except Exception as e:
        logger.error(f"Error ingesting files: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

import logging
import traceback
from fastapi import APIRouter

from app.services.multi_agent.multi_agent_service import execute_multi_agent
from app.models.request_models import MultiAgentRequest
from app.models.response_models import MultiAgentResponse, AnswerMessage
from app.utils.exceptions import ExecutingException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", tags=["Multi agent"], description="Chat with a complex multi-agent system.")
async def chat(request: MultiAgentRequest) -> MultiAgentResponse:
    """Chat with a complex multi-agent system."""
    try:
        response = await execute_multi_agent(request.tid, request.input)
        return MultiAgentResponse(
            status=200,
            message="",
            data= AnswerMessage(tid=request.tid, output=response))
    except Exception as e:
        logger.error("Error in execute multi-agent API", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=request.tid,
            output="Error in execute multi-agent API",
            detail=traceback.format_exc()
        )



from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.core.utils.streaming import to_sse
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.base import ResponseWrapper
from app.services.multi_agent.core.multi_agent_service import MultiAgentService
from app.services.multi_agent.deps import get_multi_agent_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/multi-agent", tags=["Multi agent"])


@router.post("/chat", summary="Chat with a complex multi-agent system.", response_model=ResponseWrapper[AgentChatResponse])
async def chat(
    request: AgentChatRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
):
    response = await multi_agent_service.execute_multi_agent(request.thread_id, request.input)
    return response.to_response()


@router.post("/stream", summary="Stream chat with a complex multi-agent system.", response_class=EventSourceResponse)
async def stream(
    request: AgentChatRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
):
    response = await multi_agent_service.stream_multi_agent(request.thread_id, request.input)
    return EventSourceResponse(to_sse(response))

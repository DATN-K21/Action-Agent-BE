from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.dependencies import get_multi_agent_service
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.multi_agent.multi_agent_service import MultiAgentService
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/chat", description="Chat with a complex multi-agent system.", response_model=ResponseWrapper[ChatResponse])
async def chat(
    request: ChatRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
):
    response = await multi_agent_service.execute_multi_agent(request.thread_id, request.input)
    return response.to_response()


@router.post("/stream", description="Stream chat with a complex multi-agent system.", response_class=EventSourceResponse)
async def stream(
    request: ChatRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service),
):
    response = await multi_agent_service.stream_multi_agent(request.thread_id, request.input)
    return EventSourceResponse(to_sse(response))

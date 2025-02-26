from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.core.agents.agent import Agent
from app.core.agents.deps import get_chat_agent
from app.dependencies import get_chatbot_service
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatRequest, ChatResponse
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/chat", description="Simple chat with LLM model.", response_model=ResponseWrapper[ChatResponse])
async def chat(
    request: ChatRequest,
    chat_agent: Agent = Depends(get_chat_agent),
):
    response = await chat_agent.execute_chatbot(request.thread_id, request.input)
    return response.to_response()


@router.post("/stream", description="Stream chat with LLM model.", response_model=ResponseWrapper[ChatResponse])
async def stream(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    response = await chatbot_service.stream_chatbot(request.thread_id, request.input)
    return EventSourceResponse(to_sse(response))

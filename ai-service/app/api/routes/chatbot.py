from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.dependencies import get_chatbot_service
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chatbot_service import ChatbotService
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/chat", description="Simple chat with LLM model.", response_model=ResponseWrapper[ChatResponse])
async def chat(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    response = await chatbot_service.execute_chatbot(request.threadId, request.input)
    return response.to_response()


@router.post("/stream", description="Stream chat with LLM model.", response_class=EventSourceResponse)
async def stream(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    response = await chatbot_service.stream_chatbot(request.threadId, request.input)
    return EventSourceResponse(to_sse(response))

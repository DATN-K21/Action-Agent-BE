import logging
import traceback

from fastapi import APIRouter
from app.services.chatbot_service import execute_chatbot

from app.models.request_models import ChatbotRequest
from app.models.response_models import ChatbotResponse, AnswerMessage
from app.utils.exceptions import ExecutingException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", tags=["Chatbot"], description="Simple chat with LLM model.")
async def chat(request: ChatbotRequest) -> ChatbotResponse:
    try:
        response = await execute_chatbot(request.tid, request.input)
        return ChatbotResponse(
            status=200,
            message="",
            data=AnswerMessage(
                tid=request.tid,
                output=response))
    except Exception as e:
        logger.error("An unexpected error occurred.", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=request.tid,
            output="Error in execute chatbot API",
            detail=traceback.format_exc())

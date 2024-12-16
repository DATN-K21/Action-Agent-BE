import traceback
import logging
from fastapi import APIRouter

from app.models.request_models import SearchBotRequest
from app.models.response_models import SearchBotResponse, AnswerMessage
from app.services.search_service import execute_search

from app.models.response_model import SearchBotResponse, AnswerMessage
from app.utils.exceptions import ExecutingException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", description="Chat with the search assistant.")
async def chat(request: SearchBotRequest) -> SearchBotResponse:
    """Chat with the search assistant."""
    try:
        response = await execute_search(request.tid, request.input)
        return SearchBotResponse(
            status=200,
            message="",
            data=AnswerMessage(
                tid=request.tid,
                output=response))
    except Exception as e:
        logger.error("Error in execute RAG API.", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=request.tid,
            output="Error in execute RAG API",
            detail=traceback.format_exc())
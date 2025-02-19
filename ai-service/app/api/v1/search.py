from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.dependencies import get_identity_service, get_search_service
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.search_service import SearchService
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/chat", description="Chat with the search assistant.", response_model=ResponseWrapper[ChatResponse])
async def chat(
    request: ChatRequest,
    search_service: SearchService = Depends(get_search_service),
    identity_service=Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    response = await search_service.execute_search(request.threadId, request.input)
    return response.to_response()

@router.post("/stream", description="Stream chat with the search assistant.", response_class=EventSourceResponse)
async def stream(
    request: ChatRequest,
    search_service: SearchService = Depends(get_search_service),
    identity_service=Depends(get_identity_service),
):
    if identity_service.user_id() == "":
        return ResponseWrapper.wrap(status=401, message="Unauthorized")
    response = await search_service.stream_search(request.threadId, request.input)
    return EventSourceResponse(to_sse(response))

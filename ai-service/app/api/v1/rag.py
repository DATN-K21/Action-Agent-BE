from typing import BinaryIO, cast

from fastapi import APIRouter, Depends, Form, UploadFile
from langchain_core.documents.base import Blob
from langchain_core.runnables import RunnableConfig
from sse_starlette import EventSourceResponse

from app.core import logging
from app.dependencies import get_identity_service, get_rag_service
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.ingest import IngestResponse
from app.services.identity_service import IdentityService
from app.services.rag_service import RagService
from app.utils.streaming import to_sse
from app.utils.uploading import convert_ingestion_input_to_blob, ingest_runnable

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/ingest", description="Upload files to the given thread.", response_model=ResponseWrapper[IngestResponse])
async def ingest_files(
    files: list[UploadFile],
    threadId: str = Form(...),
    identity_service: IdentityService = Depends(get_identity_service),
):
    file_blobs: list[Blob] = [convert_ingestion_input_to_blob(file) for file in files]
    config = RunnableConfig(configurable={"thread_id": threadId})
    ingest_runnable.batch(cast(list[BinaryIO], file_blobs), config)
    response_data = IngestResponse(threadId=threadId, isSuccess=True, output="Files ingested successfully")
    return ResponseWrapper.wrap(status=200, data=response_data).to_response()


@router.post("/chat", description="Chat with the RAG assistant.", response_model=ResponseWrapper[ChatResponse])
async def chat(
    request: ChatRequest,
    rag_service: RagService = Depends(get_rag_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    response = await rag_service.execute_rag(request.threadId, request.input)
    return response.to_response()


@router.post("/stream", description="Stream chat with the RAG assistant.", response_class=EventSourceResponse)
async def stream(
    request: ChatRequest,
    rag_service: RagService = Depends(get_rag_service),
    identity_service: IdentityService = Depends(get_identity_service),
):
    response = await rag_service.stream_rag(request.threadId, request.input)
    return EventSourceResponse(to_sse(response))

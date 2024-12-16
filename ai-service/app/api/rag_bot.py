import traceback
import logging
from fastapi import APIRouter, UploadFile, Form

from app.services.rag_service import execute_rag
from app.utils.upload import convert_ingestion_input_to_blob, ingest_runnable

from app.models.request_models import RagBotRequest
from app.models.response_models import RagBotResponse, IngestFileResponse, AnswerMessage
from app.utils.exceptions import ExecutingException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest", description="Upload files to the given thread.")
def ingest_files(
        files: list[UploadFile],
        tid: str = Form(...),
) -> IngestFileResponse:
    """Ingest a list of files."""
    try:
        file_blobs = [convert_ingestion_input_to_blob(file) for file in files]
        ingest_runnable.batch(file_blobs, {"thread_id": tid})
        return IngestFileResponse(
            status=200,
            message="",
            data=AnswerMessage(
                tid=tid,
                output="Files ingested successfully"))
    except Exception as e:
        logger.error("Error in ingest files API.", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=tid,
            output="Error in ingest files API",
            detail=traceback.format_exc())

@router.post("/chat", description="Chat with the RAG assistant.")
async def chat(request: RagBotRequest) -> RagBotResponse:
    """Chat with the RAG assistant."""
    try:
        response = await execute_rag(request.tid, request.input)
        return RagBotResponse(
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
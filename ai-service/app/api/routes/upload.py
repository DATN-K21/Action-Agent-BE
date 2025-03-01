from typing import BinaryIO, cast

from fastapi import APIRouter, Depends, Form, UploadFile
from langchain_core.documents.base import Blob
from langchain_core.runnables import RunnableConfig

from app.core import logging
from app.schemas.base import ResponseWrapper
from app.schemas.ingest import IngestResponse
from app.utils.uploading import convert_ingestion_input_to_blob, ingest_runnable

logger = logging.get_logger(__name__)

router = APIRouter()

@router.post("/ingest", tags=["Upload"], description="Upload files to the given thread.", response_model=ResponseWrapper[IngestResponse])
async def ingest_files(
    files: list[UploadFile],
    threadId: str = Form(...),
):
    try:
        file_blobs: list[Blob] = [convert_ingestion_input_to_blob(file) for file in files]
        config = RunnableConfig(configurable={"thread_id": threadId})
        ingest_runnable.batch(cast(list[BinaryIO], file_blobs), config)
        response_data = IngestResponse(thread_id=threadId, is_success=True, output="Files ingested successfully")
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Error ingesting files: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
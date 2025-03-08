from typing import BinaryIO, cast

from fastapi import APIRouter, Depends, Form, UploadFile
from langchain_core.documents.base import Blob
from langchain_core.runnables import RunnableConfig

from app.api.deps import AuthContext
from app.core import logging
from app.core.utils.uploading import convert_ingestion_input_to_blob, ingest_runnable
from app.schemas.base import ResponseWrapper
from app.schemas.ingest import IngestResponse

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post(
    "/{user_id}/{thread_id}/upload",
    summary="Upload files to the given thread.",
    response_model=ResponseWrapper[IngestResponse],
)
async def ingest_files(
    thread_id: str,
    user_id: str,
    files: list[UploadFile] = Form(...),
    auth_context: AuthContext = Depends(),
):
    try:
        auth_context.ensure_user_id(user_id)
        # TODO: check if userid-threadid exists
        # Call db to find (userId, threadId)

        file_blobs: list[Blob] = [convert_ingestion_input_to_blob(file) for file in files]
        config = RunnableConfig(configurable={"thread_id": thread_id})
        ingest_runnable.batch(cast(list[BinaryIO], file_blobs), config)
        response_data = IngestResponse(
            user_id=user_id, thread_id=thread_id, is_success=True, output="Files ingested successfully"
        )
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Error ingesting files: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

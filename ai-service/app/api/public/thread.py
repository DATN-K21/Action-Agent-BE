from typing import BinaryIO, cast

from fastapi import APIRouter, Depends, Form, UploadFile
from langchain_core.documents.base import Blob
from langchain_core.runnables import RunnableConfig

from app.api.deps import ensure_user_id
from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.utils.convert_messages_to_dict import convert_messages_to_dicts
from app.core.utils.uploading import convert_ingestion_input_to_blob, ingest_runnable
from app.schemas.base import CursorPagingRequest, ResponseWrapper
from app.schemas.history import GetHistoryResponse
from app.schemas.ingest import IngestFileResponse
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    DeleteThreadResponse,
    GetListThreadsResponse,
    GetThreadResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
)
from app.services.database.deps import get_thread_service
from app.services.database.thread_service import ThreadService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/thread", tags=["Thread"])


@router.post("/{user_id}/get-all", summary="Get threads of a user.", response_model=ResponseWrapper[GetListThreadsResponse])
async def get_all_threads(
    user_id: str,
    paging: CursorPagingRequest = Depends(),
    thread_service: ThreadService = Depends(get_thread_service),
    _: bool = Depends(ensure_user_id),
):
    response = await thread_service.get_all_threads(user_id, paging)
    return response.to_response()


@router.post("/{user_id}/create", summary="Create a new thread.", response_model=ResponseWrapper[CreateThreadResponse])
async def create_new_thread(
    user_id: str,
    request: CreateThreadRequest,
    thread_service: ThreadService = Depends(get_thread_service),
    _: bool = Depends(ensure_user_id),
):
    response = await thread_service.create_thread(user_id, request)
    return response.to_response()


@router.get("/{user_id}/{thread_id}/get-detail", summary="Get thread details.", response_model=ResponseWrapper[GetThreadResponse])
async def get_thread_by_id(
    user_id: str,
    thread_id: str,
    thread_service: ThreadService = Depends(get_thread_service),
    _: bool = Depends(ensure_user_id),
):
    response = await thread_service.get_thread_by_id(user_id, thread_id)
    return response.to_response()


@router.patch("/{user_id}/{thread_id}/update", summary="Update thread inf.", response_model=ResponseWrapper[UpdateThreadResponse])
async def update_thread(
    user_id: str,
    thread_id: str,
    thread: UpdateThreadRequest,
    thread_service: ThreadService = Depends(get_thread_service),
    _: bool = Depends(ensure_user_id),
):
    response = await thread_service.update_thread(user_id, thread_id, thread)
    return response.to_response()


@router.delete("/{user_id}/{thread_id}/delete", summary="Delete a thread.", response_model=ResponseWrapper[DeleteThreadResponse])
async def delete_thread(
    user_id: str,
    thread_id: str,
    thread_service: ThreadService = Depends(get_thread_service),
    _: bool = Depends(ensure_user_id),
):
    response = await thread_service.delete_thread(user_id, thread_id, user_id)
    return response.to_response()


@router.get("/{user_id}/{thread_id}/get-history", summary="Get thread chat.", response_model=ResponseWrapper[GetHistoryResponse])
async def get_state(
    user_id: str,
    thread_id: str,
    agent_manager: AgentManager = Depends(get_agent_manager),
    _: bool = Depends(ensure_user_id),
):
    try:
        agent = agent_manager.get_agent(name="chat-agent")
        state = await agent.async_get_state(thread_id)  # type: ignore

        if "messages" in state.values:
            response_data = convert_messages_to_dicts(state.values["messages"])
            return ResponseWrapper.wrap(status=200, data=GetHistoryResponse(messages=list(response_data))).to_response()
    except Exception as e:
        logger.error(f"Error ingesting files: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/{user_id}/{thread_id}/upload", summary="Upload file to thread", response_model=ResponseWrapper[IngestFileResponse])
async def upload_files(
    user_id: str,
    thread_id: str,
    file: UploadFile = Form(...),
    _: bool = Depends(ensure_user_id),
):
    try:
        # TODO: check if userid-threadid exists
        # Call db to find (userId, threadId)

        file_blob: Blob = convert_ingestion_input_to_blob(file)
        config = RunnableConfig(configurable={"thread_id": thread_id})
        ingest_runnable.batch(cast(list[BinaryIO], [file_blob]), config)
        response_data = IngestFileResponse(
            user_id=user_id, thread_id=thread_id, is_success=True, output="Files ingested successfully"
        )
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error ingesting files: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
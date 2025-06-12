import logging
import os
import shutil
import uuid
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import IO, Annotated, Any

import aiofiles
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.deps import SessionDep
from app.core.constants import SYSTEM
from app.core.enums import AssistantType, UploadStatus, WorkflowType
from app.core.settings import env_settings
from app.db_models.assistant import Assistant
from app.db_models.member_upload_link import MemberUploadLink
from app.db_models.team import Team
from app.db_models.upload import Upload
from app.db_models.upload_thread_link import UploadThreadLink
from app.jobs.tasks import add_upload, edit_upload, perform_search, remove_upload
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.upload import CreateUploadRequest, UploadResponse, UploadsResponse

router = APIRouter(prefix="/upload", tags=["Upload"])

logger = logging.getLogger(__name__)


async def _alink_upload_to_assistant_members(session: SessionDep, upload_id: str, thread_id: str, user_id: str) -> None:
    """
    Link upload to appropriate assistant members based on assistant type.

    For General Assistant:
    - Add upload to root member of main team (chatbot team)
    - Add upload to root member of RAG team

    For Advanced Assistant:
    - Add upload to chatbot assistant member of main team
    - Add upload to root member of RAG team

    Args:
        session: Database session
        upload_id: ID of the upload to link
        thread_id: ID of the thread
        user_id: User ID
    """
    try:
        # Get thread with assistant
        from app.db_models.thread import Thread

        thread_statement = (
            select(Thread)
            .options(selectinload(Thread.assistant).selectinload(Assistant.teams).selectinload(Team.members))
            .where(Thread.id == thread_id, Thread.is_deleted.is_(False))
        )

        thread_result = await session.execute(thread_statement)
        thread = thread_result.scalar_one_or_none()

        if not thread or not thread.assistant:
            logger.warning(f"Thread {thread_id} or assistant not found for upload linking")
            return

        assistant = thread.assistant

        # Find target members based on assistant type
        members_to_link = []

        if assistant.assistant_type == AssistantType.GENERAL_ASSISTANT:
            # For general assistant: get root member of main team (chatbot) and root member of RAG team
            for team in assistant.teams:
                if team.workflow_type == WorkflowType.CHATBOT or team.workflow_type == WorkflowType.RAGBOT:
                    for member in team.members:
                        members_to_link.append(member.id)

        elif assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
            # For advanced assistant: get chatbot member of main team and root member of RAG team
            for team in assistant.teams:
                if team.workflow_type == WorkflowType.HIERARCHICAL:
                    # Main team - find chatbot member
                    for member in team.members:
                        if member.type == "worker" and "chatbot" in member.name.lower() and member.created_by == SYSTEM:
                            members_to_link.append(member.id)
                            break
                elif team.workflow_type == WorkflowType.RAGBOT:
                    # RAG team - find root member
                    for member in team.members:
                        members_to_link.append(member.id)

        # Create member-upload links
        for member_id in members_to_link:
            member_upload_link = MemberUploadLink(member_id=member_id, upload_id=upload_id)
            session.add(member_upload_link)

        await session.flush()
        logger.info(f"Upload {upload_id} linked to {len(members_to_link)} members")

    except Exception as e:
        logger.error(f"Error linking upload to assistant members: {e}", exc_info=True)
        # Don't raise the exception to avoid breaking the upload creation process


async def _valid_content_length(
    content_length: int = Header(..., le=env_settings.MAX_UPLOAD_SIZE),
) -> int:
    return content_length


def _save_file_if_within_size_limit(file: UploadFile, file_size: int) -> IO[bytes]:
    """
    Check if the uploaded file size is smaller than the specified file size.
    This is to restrict an attacker from sending a valid Content-Length header and a
    body bigger than what the app can take.
    If the file size exceeds the limit, raise an HTTP 413 error. Otherwise, save the file
    to a temporary location and return the temporary file.

    Args:
        file (UploadFile): The file uploaded by the user.
        file_size (int): The file size in bytes.

    Raises:
        HTTPException: If the file size exceeds the maximum allowed size.

    Returns:
        IO: A temporary file containing the uploaded data.
    """
    # Check file size
    real_file_size = 0
    temp: IO[bytes] = NamedTemporaryFile(delete=False)
    for chunk in file.file:
        real_file_size += len(chunk)
        if real_file_size > file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large"
            )
        temp.write(chunk)
    temp.close()
    return temp


def _move_upload_to_shared_folder(filename: str, temp_file_dir: str) -> str:
    """
    Move an uploaded file to a shared folder with a unique name and set its permissions.

    Args:
        filename (str): The original name of the uploaded file.
        temp_file_dir (str): The directory of the temporary file.

    Returns:
        str: The new file path in the shared folder.
    """
    file_name = f"{uuid.uuid4()}-{filename}"
    file_path = f"./app/shared_folder/{file_name}"
    shutil.move(temp_file_dir, file_path)
    os.chmod(file_path, 0o775)
    return file_path


@router.get("/", response_model=ResponseWrapper[UploadsResponse])
async def aread_uploads(
    session: SessionDep,
    status: UploadStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Retrieve uploads.
    """
    filters = []
    if status:
        filters.append(Upload.status == status)
    if x_user_role not in ["admin", "super_admin"]:
        filters.append(Upload.user_id == x_user_id)
    filters.append(Upload.is_deleted.is_(False))

    # Only apply where clause if there are filters, otherwise return all rows
    if filters:
        filter_conditions = and_(*filters)
        count_statement = select(func.count()).select_from(Upload).where(filter_conditions)
        statement = select(Upload).where(filter_conditions).offset(skip).limit(limit)
    else:
        count_statement = select(func.count()).select_from(Upload).where(Upload.is_deleted.is_(False))
        statement = select(Upload).where(Upload.is_deleted.is_(False)).offset(skip).limit(limit)

    result = await session.execute(count_statement)
    count = result.scalar_one()

    result = await session.execute(statement)
    uploads = result.scalars().all()

    response_data = [UploadResponse.model_validate(upload) for upload in uploads]

    return ResponseWrapper.wrap(
        status=200,
        data=UploadsResponse(
            uploads=response_data,
            count=count,
        ),
    ).to_response()


def _get_file_type(filename: str) -> str:
    extension = filename.split(".")[-1].lower()
    file_types = {
        "pdf": "pdf",
        "docx": "docx",
        "pptx": "pptx",
        "xlsx": "xlsx",
        "txt": "txt",
        "html": "html",
        "md": "md",
    }
    return file_types.get(extension, "unknown")


@router.post("/", response_model=ResponseWrapper[UploadResponse])
async def acreate_upload(
    session: SessionDep,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    file_type: Annotated[str, Form()],
    chunk_size: Annotated[int, Form()],
    chunk_overlap: Annotated[int, Form()],
    web_url: Annotated[str | None, Form()] = None,
    thread_id: str | None = Form(None),
    file: UploadFile | None = None,
    x_user_id: str = Header(None),
) -> Any:
    """Create upload"""
    logger.info(f"Received upload request: file_type={file_type}, name={name}")

    try:
        if file_type not in ["file", "web"]:
            return ResponseWrapper.wrap(status=400, message=f"Invalid file type: {file_type}").to_response()

        if file_type == "web" and not web_url:
            return ResponseWrapper.wrap(status=400, message="Web URL is required for web uploads").to_response()

        if file_type == "file" and not file:
            return ResponseWrapper.wrap(status=400, message="File is required for file uploads").to_response()

        try:
            chunk_size = int(chunk_size)
            chunk_overlap = int(chunk_overlap)
            if chunk_size <= 0 or chunk_overlap < 0:
                return ResponseWrapper.wrap(
                    status=400,
                    message="Chunk size must be greater than 0 and chunk overlap must be non-negative",
                ).to_response()
        except ValueError:
            return ResponseWrapper.wrap(status=400, message="Invalid chunk size or overlap").to_response()

        if file_type == "file":
            if file and file.filename:
                actual_file_type = _get_file_type(file.filename)
                if actual_file_type == "unknown":
                    return ResponseWrapper.wrap(status=400, message="Unsupported file type").to_response()
            else:
                return ResponseWrapper.wrap(status=400, message="File name is required for file uploads").to_response()
        else:
            actual_file_type = "web"

        upload_request = CreateUploadRequest(
            name=name,
            description=description,
            file_type=actual_file_type,
            web_url=web_url if web_url else "",
            thread_id=thread_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        upload = Upload(
            name=upload_request.name,
            description=upload_request.description,
            file_type=upload_request.file_type,
            web_url=upload_request.web_url,
            thread_id=upload_request.thread_id,
            chunk_size=upload_request.chunk_size,
            chunk_overlap=upload_request.chunk_overlap,
            user_id=x_user_id,
            status=UploadStatus.IN_PROGRESS,
        )

        session.add(upload)
        await session.commit()
        await session.refresh(upload)

        if upload.id is None:
            raise HTTPException(status_code=500, detail="Failed to create upload")

        if thread_id is not None:
            # Associate upload with thread if thread_id is provided
            from app.db_models.thread import Thread

            # Check if thread exists
            thread_statement = select(Thread).where(Thread.id == thread_id, Thread.is_deleted.is_(False))

            thread_result = await session.execute(thread_statement)
            thread = thread_result.scalar_one_or_none()

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            # Create link between upload and thread
            link = UploadThreadLink(upload_id=upload.id, thread_id=thread_id)
            session.add(link)
            await session.commit()
            await session.refresh(link)

            # Link upload to appropriate assistant members based on assistant type
            await _alink_upload_to_assistant_members(session, upload.id, thread_id, x_user_id)

        if file_type == "web":
            # Handle web upload
            add_upload.delay(web_url, upload.id, x_user_id, chunk_size, chunk_overlap)
        else:
            # Handle file upload
            if not file or not file.filename:
                raise HTTPException(status_code=400, detail="File is required")

            file_path = await save_upload_file(file)
            add_upload.delay(file_path, upload.id, x_user_id, chunk_size, chunk_overlap)

        logger.info(f"Upload created successfully: id={upload.id}")
        return upload

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        if "upload" in locals():
            await session.delete(upload)
            await session.commit()
        return ResponseWrapper.wrap(status=500, message=f"Failed to process upload: {str(e)}").to_response()


async def save_upload_file(file: UploadFile) -> str:
    file_name = f"{uuid.uuid4()}-{file.filename}"
    file_path = f"./app/{file_name}"

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    os.chmod(file_path, 0o775)
    return file_path


@router.put("/{upload_id}", response_model=ResponseWrapper[UploadResponse])
async def aupdate_upload(
    session: SessionDep,
    upload_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    file_type: str | None = Form(None),
    chunk_size: Annotated[int, Form(ge=0)] | None = Form(None),
    chunk_overlap: Annotated[int, Form(ge=0)] | None = Form(None),
    web_url: str | None = Form(None),
    file: UploadFile | None = File(None),
    file_size: int = Depends(_valid_content_length),
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """Update upload"""
    statement = select(Upload).where(Upload.id == upload_id, Upload.is_deleted.is_(False))

    result = await session.execute(statement)
    upload = result.scalar_one_or_none()

    if not upload:
        return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()
    if x_user_role not in ["admin", "super admin"] and upload.user_id != x_user_id:
        return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()

    update_data: dict[str, Any] = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if file_type is not None:
        update_data["file_type"] = file_type
    if web_url is not None:
        update_data["web_url"] = web_url
    if chunk_size is not None:
        update_data["chunk_size"] = chunk_size
    if chunk_overlap is not None:
        update_data["chunk_overlap"] = chunk_overlap

    if update_data:
        update_data["last_modified"] = datetime.now()
        for key, value in update_data.items():
            setattr(upload, key, value)
        session.add(upload)
        await session.commit()

    if file_type == "web" and web_url:
        # Handle web update
        setattr(upload, "status", UploadStatus.IN_PROGRESS)
        session.add(upload)
        await session.commit()
        edit_upload.delay(
            web_url,
            id,
            upload.user_id,
            chunk_size or upload.chunk_size,
            chunk_overlap or upload.chunk_overlap,
        )
    elif file:
        # Handle file update
        if file.content_type not in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
            "text/html",
            "text/markdown",
        ]:
            return ResponseWrapper.wrap(status=400, message="Invalid file type. Supported types: pdf, docx, pptx, xlsx, txt, html, md").to_response()

        temp_file = _save_file_if_within_size_limit(file, file_size)
        if upload.user_id is None:
            return ResponseWrapper.wrap(status=500, message="Failed to retrieve owner ID").to_response()

        setattr(upload, "status", UploadStatus.IN_PROGRESS)
        session.add(upload)
        await session.commit()

        if not file.filename or not isinstance(temp_file.name, str):
            raise HTTPException(status_code=500, detail="Failed to upload file")

        file_path = _move_upload_to_shared_folder(file.filename, temp_file.name)
        edit_upload.delay(
            file_path,
            id,
            upload.user_id,
            chunk_size or upload.chunk_size,
            chunk_overlap or upload.chunk_overlap,
        )

    await session.commit()
    await session.refresh(upload)

    response_data = UploadResponse.model_validate(upload)
    return ResponseWrapper.wrap(status=200, data=response_data).to_response()


@router.delete("/{upload_id}", response_model=ResponseWrapper[MessageResponse])
async def adelete_upload(session: SessionDep, upload_id: str, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    statement = select(Upload).where(
        Upload.id == upload_id,
        Upload.is_deleted.is_(False),
    )

    result = await session.execute(statement)
    upload = result.scalar_one_or_none()

    if not upload:
        return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()
    if x_user_role not in ["admin", "super admin"] and upload.user_id != x_user_id:
        return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()
    try:
        # Set upload status to in progress
        setattr(upload, "status", UploadStatus.IN_PROGRESS)
        session.add(upload)
        await session.commit()

        if upload.user_id is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve owner ID")

        remove_upload.delay(id, upload.user_id)
    except Exception as e:
        logger.error(f"Error deleting upload: {str(e)}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message=f"Failed to delete upload: {str(e)}").to_response()

    response_data = MessageResponse(message="Upload deletion initiated successfully")
    return ResponseWrapper.wrap(status=200, data=response_data).to_response()


@router.post("/{upload_id}/search")
async def asearch_upload(
    session: SessionDep,
    upload_id: str,
    search_params: dict[str, Any],
    x_user_id: str = Header(None),
):
    """
    Initiate an asynchronous search within a specific upload.
    """
    statement = select(Upload).where(
        Upload.id == upload_id,
        Upload.is_deleted.is_(False),
    )

    result = await session.execute(statement)
    upload = result.scalar_one_or_none()

    if not upload:
        return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()
    if x_user_id not in ["admin", "super admin"] and upload.user_id != x_user_id:
        return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()

    search_type = search_params.get("search_type", "vector")
    if search_type not in ["vector", "fulltext", "hybrid"]:
        return ResponseWrapper.wrap(status=400, message="Invalid search type. Supported types: vector, fulltext, hybrid").to_response()

    task = perform_search.delay(
        x_user_id,
        upload_id,
        search_params["query"],
        search_type,
        search_params.get("top_k", 5),
        search_params.get("score_threshold", 0.5),
    )

    return {"task_id": task.id}


@router.get("/{upload_id}/search/{task_id}")
async def aget_search_results(task_id: str):
    """
    Retrieve the results of an asynchronous search task.
    """
    task_result = AsyncResult(task_id)
    if task_result.ready():
        return {"status": "completed", "results": task_result.result}
    else:
        return {"status": "pending"}

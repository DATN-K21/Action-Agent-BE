import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.celery import celery_app
from app.core import logging
from app.core.constants import SYSTEM
from app.core.enums import AssistantType, UploadStatus, WorkflowType
from app.core.settings import env_settings
from app.db_models.assistant import Assistant
from app.db_models.member_upload_link import MemberUploadLink
from app.db_models.team import Team
from app.db_models.thread import Thread
from app.db_models.upload import Upload
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.upload import (
    UploadInitiateRequest,
    UploadInitiateResponse,
    UploadResponse,
    UploadsResponse,
    UploadStatusResponse,
)
from app.services import get_blob_storage_service

router = APIRouter(prefix="/uploads", tags=["Uploads"])

logger = logging.get_logger(__name__)


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/", response_model=ResponseWrapper[UploadsResponse])
async def aread_uploads(
    session: SessionDep,
    status: UploadStatus | None = None,
    paging: PagingRequest = Depends(),
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Retrieve uploads.
    """
    page_number = paging.page_number
    max_per_page = paging.max_per_page

    filters = []
    if status:
        filters.append(Upload.status == status)
    if x_user_role not in ["admin", "super_admin"]:
        filters.append(Upload.user_id == x_user_id)
    filters.append(Upload.is_deleted.is_(False))

    # Only apply where clause if there are filters, otherwise return all rows
    if filters:
        filter_conditions = and_(*filters)
        statement = select(Upload).where(filter_conditions).offset((page_number - 1) * max_per_page).limit(max_per_page)
    else:
        statement = select(Upload).where(Upload.is_deleted.is_(False)).offset((page_number - 1) * max_per_page).limit(max_per_page)

    result = await session.execute(statement)
    uploads = result.scalars().all()

    response_data = [UploadResponse.model_validate(upload) for upload in uploads]

    return ResponseWrapper.wrap(
        status=200,
        data=UploadsResponse(uploads=response_data),
    ).to_response()


@router.delete("/{upload_id}", response_model=ResponseWrapper)
async def adelete_upload(
    session: SessionDep,
    upload_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
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
    if upload.status not in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
        return ResponseWrapper.wrap(status=400, message="Upload must be completed or failed before deletion").to_response()

    try:
        # Soft-delete upload record
        upload.is_deleted = True
        session.add(upload)
        await session.commit()

        # Enqueue upload removal task to ingest-service
        celery_app.send_task(
            "ingest.document.remove",
            args=[upload_id, upload.user_id],
            queue="document.processing",
        )

        return ResponseWrapper.wrap(status=202, data=None).to_response()
    except Exception as e:
        logger.error(f"Error deleting upload: {str(e)}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message=f"Failed to delete upload: {str(e)}").to_response()


@router.post("/initiate", response_model=ResponseWrapper[UploadInitiateResponse])
async def ainitiate_upload(
    session: SessionDep,
    request: UploadInitiateRequest,
    x_user_id: str = Header(None),
) -> Any:
    """
    Initiate a new direct upload to Azure Blob Storage using append blobs.

    This endpoint:
    1. Validates the file size against limits
    2. Creates an Upload record in the database with status "Uploading"
    3. Generates an append-blob SAS URL for direct client upload
    4. Returns upload instructions and metadata

    The client should then upload directly to Azure using the returned SAS URL.
    After upload completes, call /uploads/{upload_id}/process to trigger processing.
    """
    try:
        # Validate file size before creating any resources
        max_file_size_mb = env_settings.MAX_UPLOAD_SIZE_MB
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        if request.file_size_bytes > max_file_size_bytes:
            return ResponseWrapper.wrap(
                status=400, message=f"File size ({request.file_size_bytes} bytes) exceeds maximum limit of {max_file_size_mb}MB"
            ).to_response()

        # Validate filename and get file type
        if not request.filename or not request.filename.strip():
            return ResponseWrapper.wrap(status=400, message="Filename is required").to_response()

        actual_file_type = _get_file_type(request.filename)
        if actual_file_type == "unknown":
            return ResponseWrapper.wrap(
                status=400,
                message="Unsupported file type. Only support: pdf, docx, pptx, xlsx, txt, html, md",
            ).to_response()

        # Validate other parameters
        if request.chunk_size <= 0 or request.chunk_overlap < 0:
            return ResponseWrapper.wrap(
                status=400,
                message="Chunk size must be greater than 0 and chunk overlap must be non-negative",
            ).to_response()

        unique_id = uuid.uuid4()

        # Generate append-blob SAS URL
        blob_service = get_blob_storage_service()
        upload_info = await blob_service.generate_append_blob_sas(
            f"{unique_id}-{request.filename}",
            expiry_hours=1,
            max_file_size_mb=max_file_size_mb,
        )

        # Debug: Log the upload_info to see what's being returned
        logger.info(f"Upload info from blob service: {upload_info}")

        # Set is_global based on whether thread_id is provided
        is_global = request.thread_id is None

        if not is_global:
            thread_statement = select(Thread).where(Thread.id == request.thread_id, Thread.is_deleted.is_(False))
            thread_result = await session.execute(thread_statement)
            thread = thread_result.scalar_one_or_none()
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

        # Create Upload record in database
        upload = Upload(
            id=str(unique_id),
            name=request.name,
            description=request.description,
            file_type=actual_file_type,
            web_url=upload_info["blob_url"],  # Store the final blob URL
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            user_id=x_user_id,
            status=UploadStatus.UPLOADING,  # Set to uploading - file is being uploaded to Azure
            is_global=is_global,
            thread_id=request.thread_id,  # Set thread_id directly (None for global uploads)
        )

        session.add(upload)
        await session.flush()
        await session.refresh(upload)
        if upload.id is None:
            raise HTTPException(status_code=500, detail="Failed to create upload record")

        # Handle upload-thread relationships based on global/private nature
        if not is_global:
            # Private upload: validate thread exists and link to assistant members
            await _alink_upload_to_assistant_members(session, upload.id, request.thread_id, x_user_id)  # type: ignore

        await session.commit()

        # Note: Processing will be triggered later when client calls /uploads/{id}/process
        # after successful upload to Azure

        # Prepare response
        response_data = UploadInitiateResponse(
            upload_id=upload.id,
            upload_url=str(upload_info["upload_url"]),
            blob_url=str(upload_info["blob_url"]),
            blob_name=str(upload_info["blob_name"]),
            expires_at=str(upload_info["expires_at"]),
            max_file_size_bytes=int(upload_info["max_file_size_bytes"]),
            instructions={
                "method": "PUT",
                "headers": {
                    "x-ms-blob-type": "AppendBlob",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": "REQUIRED - Must be set by client to actual file size",
                },
                "append_blob_instructions": {
                    "step1": "Create the append blob: PUT to upload_url with x-ms-blob-type: AppendBlob and Content-Length: 0",
                    "step2": "Append data: PUT to upload_url with x-ms-blob-type: AppendBlob and your file data",
                    "note": "Or use a single PUT with the entire file content if under 4MB per block",
                },
                "note": f"Upload directly to upload_url (max {upload_info['max_file_size_bytes']}B), then call /uploads/{upload.id}/process to trigger processing",
                "size_validation": "Server will verify upload completion when you call the process endpoint.",
                "status_flow": "Uploading -> Ingesting -> Completed/Failed",
            },
        )

        # Debug: Log the response data
        logger.info(
            f"Response data created: upload_id={upload.id}, expires_at={upload_info.get('expires_at')}, max_size={upload_info.get('max_file_size_bytes', 0)}B"
        )

        logger.info(f"Initiated upload for user {x_user_id}: id={upload.id}, filename={request.filename}")
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error initiating upload: {str(e)}", exc_info=True)
        # Clean up upload record if it was created
        if "upload" in locals() and upload.id:
            try:
                await session.delete(upload)
                await session.commit()
            except Exception:
                pass
        return ResponseWrapper.wrap(status=500, message=f"Failed to initiate upload: {str(e)}").to_response()


@router.get("/{upload_id}/status", response_model=ResponseWrapper[UploadStatusResponse])
async def aget_upload_status(
    session: SessionDep,
    upload_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Get the status of an upload by checking both the database record and blob storage.

    This endpoint:
    1. Retrieves the Upload record from the database
    2. Checks the actual blob status in Azure Storage
    3. Updates the database if blob exceeds size limits
    4. Returns comprehensive status information

    Use this endpoint to monitor upload progress. After upload completes,
    call /uploads/{upload_id}/process to trigger processing.
    """
    try:
        # Get upload record from database
        statement = select(Upload).where(
            Upload.id == upload_id,
            Upload.is_deleted.is_(False),
        )

        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Check permissions
        if x_user_role not in ["admin", "super_admin"] and upload.user_id != x_user_id:
            return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()

        # Check blob status in Azure Storage
        if not upload.web_url:
            return ResponseWrapper.wrap(status=500, message="Upload record missing blob URL").to_response()

        blob_service = get_blob_storage_service()
        blob_status = await blob_service.check_blob_status(upload.web_url, max_file_size_mb=100)

        # Check blob status and update database if needed
        upload_was_updated = False
        if blob_status.get("exists", False) and blob_status.get("complete", False) and not blob_status.get("within_limits", True):
            # File exceeded size limits - mark as failed
            upload.status = UploadStatus.FAILED
            session.add(upload)
            upload_was_updated = True
            logger.warning(f"Upload {upload_id} failed due to size limit violation")

        if upload_was_updated:
            await session.commit()

        # Prepare response with proper type casting
        response_data = UploadStatusResponse(
            upload_id=upload.id,
            upload_status=upload.status,
            blob_exists=bool(blob_status.get("exists", False)),
            blob_size_bytes=int(blob_status.get("size_bytes", 0)),
            blob_size_mb=float(blob_status.get("size_mb", 0.0)),
            within_size_limits=bool(blob_status.get("within_limits", True)),
            upload_complete=bool(blob_status.get("complete", False)),
            max_file_size_bytes=int(blob_status.get("max_size_bytes", 100 * 1024 * 1024)),
            created_at=upload.created_at,
            last_modified=upload.last_modified,
        )

        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message=f"Failed to get upload status: {str(e)}").to_response()


@router.post("/{upload_id}/process", response_model=ResponseWrapper[UploadResponse])
async def aprocess_upload(
    session: SessionDep,
    upload_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Process an uploaded file after successful upload to Azure Blob Storage.

    This endpoint should be called by the client after they have successfully
    uploaded the file to Azure using the SAS URL from /initiate.

    This endpoint:
    1. Verifies the Upload record exists and belongs to the user
    2. Checks that the blob was successfully uploaded to Azure
    3. Validates the blob size is within limits
    4. Updates status to "Ingesting" and triggers the Celery processing job
    5. Returns the updated upload record

    Status flow: Uploading -> Ingesting -> Completed/Failed
    """
    try:
        # Get upload record from database
        statement = select(Upload).where(
            Upload.id == upload_id,
            Upload.is_deleted.is_(False),
        )

        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Check permissions
        if x_user_role not in ["admin", "super_admin"] and upload.user_id != x_user_id:
            return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()

        # Check if already processing or completed
        if upload.status == UploadStatus.COMPLETED:
            return ResponseWrapper.wrap(status=400, message="Upload has already been processed").to_response()

        if upload.status == UploadStatus.INGESTING:
            return ResponseWrapper.wrap(status=400, message="Upload is already being processed").to_response()

        # Verify blob exists and is valid
        if not upload.web_url:
            return ResponseWrapper.wrap(status=500, message="Upload record missing blob URL").to_response()

        blob_service = get_blob_storage_service()
        blob_status = await blob_service.check_blob_status(upload.web_url, max_file_size_mb=100)

        # Validate blob upload
        if not blob_status.get("exists", False):
            return ResponseWrapper.wrap(
                status=400, message="File not found in Azure storage. Please ensure upload completed successfully."
            ).to_response()

        if not blob_status.get("complete", False):
            return ResponseWrapper.wrap(status=400, message="File appears to be empty. Please ensure upload completed successfully.").to_response()

        if not blob_status.get("within_limits", True):
            # Mark as failed and clean up oversized blob
            upload.status = UploadStatus.FAILED
            session.add(upload)
            await session.commit()
            return ResponseWrapper.wrap(
                status=400, message=f"File exceeds size limit of {blob_status.get('max_size_mb', 100)}MB. Upload marked as failed."
            ).to_response()

        # All validations passed - trigger processing
        # Update status to ingesting before triggering Celery job
        upload.status = UploadStatus.INGESTING
        session.add(upload)
        await session.commit()

        # Enqueue upload processing task to ingest-service
        celery_app.send_task(
            "ingest.document.add",
            args=[upload.web_url, upload.id, upload.user_id, upload.chunk_size, upload.chunk_overlap],
            queue="document.processing",
        )

        logger.info(f"Processing triggered for upload {upload_id}: blob_size={blob_status.get('size_bytes', 0)} bytes")

        # Return updated upload record
        await session.refresh(upload)
        response_data = UploadResponse.model_validate(upload)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message=f"Failed to process upload: {str(e)}").to_response()


@router.post("/{upload_id}/re-initiate", response_model=ResponseWrapper[UploadInitiateResponse])
async def are_initiate_upload(
    session: SessionDep,
    upload_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Re-initiate an existing upload by generating a new SAS URL.

    This endpoint is useful when:
    - The original SAS URL expired
    - Frontend lost the SAS URL
    - Need to resume an interrupted upload

    Only works for uploads in "Uploading" status.
    """
    try:
        # Get upload record from database
        statement = select(Upload).where(
            Upload.id == upload_id,
            Upload.is_deleted.is_(False),
        )

        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Check permissions
        if x_user_role not in ["admin", "super_admin"] and upload.user_id != x_user_id:
            return ResponseWrapper.wrap(status=403, message="Not enough permissions").to_response()

        # Only allow re-initiation for uploads in "Uploading" status
        if upload.status != UploadStatus.UPLOADING:
            return ResponseWrapper.wrap(
                status=400, message=f"Cannot re-initiate upload with status '{upload.status}'. Only uploads in 'Uploading' status are eligible."
            ).to_response()

        # Extract filename from the existing blob URL for regeneration
        if not upload.web_url:
            return ResponseWrapper.wrap(status=500, message="Upload record missing blob URL").to_response()

        # Get the blob name from the existing URL to maintain consistency
        blob_name = upload.web_url.split("/")[-1]

        # Generate new SAS URL
        blob_service = get_blob_storage_service()
        upload_info = await blob_service.generate_append_blob_sas(blob_name, expiry_hours=1, max_file_size_mb=100)

        # Prepare response (same format as initiate endpoint)
        response_data = UploadInitiateResponse(
            upload_id=upload.id,
            upload_url=str(upload_info["upload_url"]),
            blob_url=str(upload_info["blob_url"]),
            blob_name=str(upload_info["blob_name"]),
            expires_at=str(upload_info["expires_at"]),
            max_file_size_bytes=int(upload_info["max_file_size_bytes"]),
            instructions={
                "method": "PUT",
                "headers": {
                    "x-ms-blob-type": "AppendBlob",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": "REQUIRED - Must be set by client to actual file size",
                },
                "append_blob_instructions": {
                    "step1": "Create the append blob: PUT to upload_url with x-ms-blob-type: AppendBlob and Content-Length: 0",
                    "step2": "Append data: PUT to upload_url with x-ms-blob-type: AppendBlob and your file data",
                    "note": "Or use a single PUT with the entire file content if under 4MB per block",
                },
                "note": f"Upload directly to upload_url (max {upload_info['max_file_size_bytes']}B), then call /uploads/{upload.id}/process to trigger processing",
                "size_validation": "Server will verify upload completion when you call the process endpoint.",
                "status_flow": "Uploading -> Ingesting -> Completed/Failed",
            },
        )

        logger.info(f"Re-initiated upload for user {x_user_id}: id={upload_id}")
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error re-initiating upload: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message=f"Failed to re-initiate upload: {str(e)}").to_response()

# =============================================================================
# Private Helper Methods
# =============================================================================
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
        thread_statement = (
            select(Thread)
            .options(selectinload(Thread.assistant).selectinload(Assistant.teams).selectinload(Team.members))
            .where(
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
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

        logger.info(f"Upload {upload_id} linked to {len(members_to_link)} members")

    except Exception as e:
        logger.error(f"Error linking upload to assistant members: {e}", exc_info=True)
        # Don't raise the exception to avoid breaking the upload creation process


def _get_file_type(filename: str) -> str:
    """
    Determine file type based on filename extension.

    Args:
        filename: The filename to check

    Returns:
        File type string or 'unknown' if not supported
    """
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return "pdf"
    elif filename.endswith(".docx"):
        return "docx"
    elif filename.endswith(".pptx"):
        return "pptx"
    elif filename.endswith(".xlsx"):
        return "xlsx"
    elif filename.endswith(".txt"):
        return "txt"
    elif filename.endswith(".html"):
        return "html"
    elif filename.endswith(".md"):
        return "md"
    else:
        return "unknown"

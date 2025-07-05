from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import UploadStatus
from app.schemas.base import BaseResponse


class UploadBase(BaseModel):
    name: str = Field(..., description="Name of the file to be uploaded")
    description: str = Field(..., description="Description of the file to be uploaded")
    file_type: str = Field(..., description="Type of the file to be uploaded (e.g., 'image', 'document', etc.)")
    web_url: str = Field(..., description="Web URL of the file to be uploaded")
    thread_id: str | None = Field(None, description="ID of the thread to which the upload is associated")

##################################################
########### REQUEST SCHEMAS ######################
##################################################

class UpdateUploadStatusRequest(BaseModel):
    """Request schema for updating upload status from ingest-service."""

    status: str = Field(..., description="New upload status")
    error_message: str | None = Field(None, description="Error message if status is failed")


class UploadInitiateRequest(BaseModel):
    """Request to initiate a new upload."""

    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    name: str = Field(..., description="Display name for the upload")
    description: str = Field(..., description="Description of the upload")
    chunk_size: int = Field(default=1000, description="Chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Chunk overlap for processing")
    thread_id: str | None = Field(None, description="Optional thread ID to link the upload")


##################################################
########### RESPONSE SCHEMAS #####################
##################################################


class UploadResponse(UploadBase, BaseResponse):
    id: str
    name: str
    description: str
    last_modified: datetime
    status: UploadStatus
    user_id: str | None
    file_type: str
    web_url: str | None
    chunk_size: int
    chunk_overlap: int


class UploadsResponse(BaseResponse):
    uploads: list[UploadResponse]


class UploadInitiateResponse(BaseResponse):
    """Response from upload initiation."""

    upload_id: str = Field(..., description="ID of the created upload record")
    upload_url: str = Field(..., description="SAS URL for direct upload to Azure Blob Storage")
    blob_url: str = Field(..., description="Final blob URL")
    blob_name: str = Field(..., description="Generated blob name")
    expires_at: str = Field(..., description="ISO timestamp when the SAS URL expires")
    max_file_size_bytes: int = Field(..., description="Maximum allowed file size in bytes")
    instructions: dict = Field(..., description="Upload instructions for the frontend")


class UploadStatusResponse(BaseResponse):
    """Response for upload status check."""

    upload_id: str = Field(..., description="ID of the upload")
    upload_status: UploadStatus = Field(..., description="Current upload status in database")
    blob_exists: bool = Field(..., description="Whether the blob exists in storage")
    blob_size_bytes: int = Field(..., description="Current blob size in bytes")
    blob_size_mb: float = Field(..., description="Current blob size in MB")
    within_size_limits: bool = Field(..., description="Whether blob is within size limits")
    upload_complete: bool = Field(..., description="Whether upload appears complete")
    max_file_size_bytes: int = Field(..., description="Maximum allowed file size in bytes")
    created_at: datetime = Field(..., description="When the upload record was created")
    last_modified: datetime = Field(..., description="When the upload was last modified")

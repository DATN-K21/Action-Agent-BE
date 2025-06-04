from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import UploadStatus
from app.schemas.base import BaseRequest, BaseResponse


class UploadBase(BaseModel):
    name: str = Field(..., description="Name of the file to be uploaded")
    description: str = Field(..., description="Description of the file to be uploaded")
    file_type: str = Field(..., description="Type of the file to be uploaded (e.g., 'image', 'document', etc.)")
    web_url: str = Field(..., description="Web URL of the file to be uploaded")


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateUploadRequest(UploadBase, BaseRequest):
    chunk_size: int = Field(..., description="Size of each chunk in bytes for file upload")
    chunk_overlap: int = Field(..., description="Overlap size in bytes for each chunk during upload")


class UpdateUploadRequest(UploadBase, BaseRequest):
    name: str | None = None
    description: str | None = None
    last_modified: datetime
    file_type: str | None = None
    web_url: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None


##################################################
########### RESPONSE SCHEMAS #####################
##################################################


class UploadResponse(UploadBase, BaseResponse):
    id: int
    name: str
    description: str
    last_modified: datetime
    status: UploadStatus
    user_id: int | None
    file_type: str
    web_url: str | None
    chunk_size: int
    chunk_overlap: int


class UploadsResponse(BaseResponse):
    uploads: list[UploadResponse]
    count: int

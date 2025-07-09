from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import UploadStatus
from app.db_models.upload import Upload
from app.schemas.base import ResponseWrapper
from app.schemas.upload import UpdateUploadStatusRequest

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.patch("/{upload_id}/status", summary="Update upload status")
async def update_upload_status(
    upload_id: str,
    request: UpdateUploadStatusRequest,
    session: SessionDep,
):
    """Internal API endpoint for updating upload status from ingest-service."""
    logger.info(f"Updating upload {upload_id} status to {request.status}")

    try:
        statement = select(Upload).where(Upload.id == upload_id, Upload.is_deleted.is_(False))
        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Try to convert string to enum
        try:
            upload_status = UploadStatus(request.status)
        except ValueError:
            return ResponseWrapper.wrap(status=400, message=f"Invalid status: {request.status}").to_response()

        upload.status = upload_status
        if upload_status == UploadStatus.FAILED:
            upload.failed_reason = request.error_message
            logger.warning(f"Upload {upload_id} failed. Error message = {request.error_message}")
        else:
            logger.info(f"Upload {upload_id} status updated to {upload_status}")

        await session.commit()
        return ResponseWrapper.wrap(status=200, data=None).to_response()

    except Exception as e:
        logger.error(f"Error updating upload status: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


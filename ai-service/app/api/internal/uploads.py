from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import UploadStatus
from app.db_models.upload import Upload
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.patch("/{upload_id}/status", summary="Update upload status")
async def update_upload_status(
    upload_id: str,
    status: UploadStatus,
    session: SessionDep,
):
    """Internal API endpoint for updating upload status from ingest-service."""
    logger.info(f"Updating upload {upload_id} status to {status}")

    try:
        statement = select(Upload).where(Upload.id == upload_id, Upload.is_deleted.is_(False))
        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Validate status directly using the enum
        if status not in UploadStatus:
            return ResponseWrapper.wrap(status=400, message=f"Invalid status: {status}").to_response()

        upload.status = status
        await session.commit()

        logger.info(f"Successfully updated upload {upload_id} status to {status}")
        return ResponseWrapper.wrap(status=200, data=None).to_response()

    except Exception as e:
        logger.error(f"Error updating upload status: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.delete("/{upload_id}", summary="Delete upload record")
async def delete_upload(
    upload_id: str,
    session: SessionDep,
):
    """Internal API endpoint for deleting upload record after vector store cleanup."""
    logger.info(f"Deleting upload record {upload_id}")

    try:
        statement = select(Upload).where(Upload.id == upload_id, Upload.is_deleted.is_(False))
        result = await session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            return ResponseWrapper.wrap(status=404, message="Upload not found").to_response()

        # Soft delete pattern instead of physically deleting
        upload.is_deleted = True
        await session.commit()

        logger.info(f"Successfully deleted upload record {upload_id}")
        return ResponseWrapper.wrap(status=200, data=None).to_response()

    except Exception as e:
        logger.error(f"Error deleting upload: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

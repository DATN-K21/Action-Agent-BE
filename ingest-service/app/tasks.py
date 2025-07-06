from app.celery_app import celery_app
from app.core import logging
from app.core.rag.pgvector import PGVectorWrapper
from app.services.ai_service_client import ai_service_client

logger = logging.get_logger(__name__)


@celery_app.task(name="ingest.document.add")
def ingest_add_upload(blob_url: str, upload_id: str, user_id: str, chunk_size: int, chunk_overlap: int) -> None:
    logger.info(f"Starting add_upload for upload_id: {upload_id}, user_id: {user_id}, blob_url: {blob_url}")

    try:
        # Process the document using vector store (only vector database operations)
        PGVectorWrapper().add(blob_url, upload_id, user_id, chunk_size, chunk_overlap)

        # Update status via AI service API
        success = ai_service_client.update_upload_status_sync(upload_id, "Completed")

        if success:
            logger.info(f"Upload {upload_id} completed successfully")
        else:
            logger.warning(f"Upload {upload_id} processed but failed to update status via API")

    except Exception as e:
        logger.error(f"add_upload failed: {e}", exc_info=True)
        # Update status to failed via AI service API
        ai_service_client.update_upload_status_sync(upload_id, "Failed", str(e))
        raise


@celery_app.task(name="ingest.document.remove")
def ingest_remove_upload(upload_id: str, user_id: str) -> None:
    logger.info(f"Starting remove_upload for upload_id: {upload_id}, user_id: {user_id}")

    try:
        # Remove from vector store only
        pgvector_store = PGVectorWrapper()
        deletion_successful = pgvector_store.delete(upload_id, user_id)

        if deletion_successful:
            logger.info(f"Upload {upload_id} removed from vector store successfully")
            # Now tell AI service to delete the upload record
            ai_service_client.delete_upload_record_sync(upload_id)
        else:
            logger.warning(f"Failed to delete documents from vector store for upload_id: {upload_id}")

    except Exception as e:
        logger.error(
            f"remove_upload failed for upload_id: {upload_id}, user_id: {user_id}. Error: {str(e)}", exc_info=True
        )
        raise

from app.core import logging
from app.core.qdrant_ingestor import LCQdrantIngestor
from app.main import celery_app
from app.services.ai_service_client import ai_service_client

log = logging.get_logger(__name__)


@celery_app.task(name="ingest.document.add", acks_late=True)
def ingest_add_upload(
    blob_url: str,
    upload_id: str,
    user_id: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> None:
    """Download → chunk → embed → upsert into Qdrant."""
    try:
        with LCQdrantIngestor() as ing:
            stored = ing.add_upload(
                blob_url,
                upload_id,
                user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        ai_service_client.update_upload_status(upload_id, "Completed", f"{stored} chunks")
    except Exception as e:
        log.exception("ingest.document.add failed")
        ai_service_client.update_upload_status(upload_id, "Failed", str(e))
        raise


@celery_app.task(name="ingest.document.remove", acks_late=True)
def ingest_remove_upload(upload_id: str, user_id: str) -> None:
    """Delete all points for (user_id, upload_id)."""
    try:
        with LCQdrantIngestor() as ing:
            ing.delete_upload(upload_id, user_id)
    except Exception:
        log.exception("ingest.document.remove failed")
        raise

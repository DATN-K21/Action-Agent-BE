import asyncio

from app.core import logging
from app.core.qdrant_ingestor import LCQdrantIngestor
from app.main import celery_app
from app.services.ai_service_client import ai_service_client

log = logging.get_logger(__name__)


# Helper to wrap an async coroutine in the current sync task
def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="ingest.document.add", acks_late=True)
def ingest_add_upload(
    blob_url: str,
    upload_id: str,
    user_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> None:
    """Download → chunk → embed → upsert into Qdrant."""

    async def _job():
        async with LCQdrantIngestor() as ing:
            stored = await ing.add_upload(
                blob_url,
                upload_id,
                user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        return stored

    try:
        stored = _run(_job())
        ai_service_client.update_upload_status(upload_id, "Completed", f"{stored} chunks")
    except Exception as e:
        log.exception("ingest.document.add failed")
        ai_service_client.update_upload_status(upload_id, "Failed", str(e))
        raise

@celery_app.task(name="ingest.document.remove", acks_late=True)
def ingest_remove_upload(upload_id: str, user_id: str) -> None:
    """Delete all points for (user_id, upload_id)."""

    async def _job():
        async with LCQdrantIngestor() as ing:
            await ing.delete_upload(upload_id, user_id)

    try:
        _run(_job())
    except Exception:
        log.exception("ingest.document.remove failed")
        raise

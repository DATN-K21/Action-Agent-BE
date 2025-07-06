"""
Celery tasks for ingestion / deletion with Qdrant backend
──────────────────────────────────────────────────────────
"""

from __future__ import annotations

import asyncio

from app.core import logging
from app.core.qdrant_ingest import QdrantIngestor
from app.main import celery_app
from app.services.ai_service_client import ai_service_client

log = logging.get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="ingest.document.add", acks_late=True)
def ingest_add_upload(
    blob_url: str, upload_id: str, user_id: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> None:
    """Download file, chunk, embed, and store in Qdrant."""
    log.info("Start ingest add - upload_id=%s user_id=%s", upload_id, user_id)
    ingestor = QdrantIngestor()
    try:
        added = _run(
            ingestor.add_upload(blob_url, upload_id, user_id, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        )
        ai_service_client.update_upload_status_sync(upload_id, "Completed", f"{added} chunks stored")
    except Exception as e:
        log.exception("ingest.add failed")
        ai_service_client.update_upload_status_sync(upload_id, "Failed", str(e))
        raise
    finally:
        _run(ingestor.aclose())


@celery_app.task(name="ingest.document.remove", acks_late=True)
def ingest_remove_upload(upload_id: str, user_id: str) -> None:
    """Delete all chunks for an upload."""
    log.info("Start ingest remove - upload_id=%s user_id=%s", upload_id, user_id)
    ingestor = QdrantIngestor()
    try:
        deleted = _run(ingestor.delete_upload(upload_id, user_id))
        if deleted:
            ai_service_client.delete_upload_record_sync(upload_id)
        else:
            log.warning("No chunks matched for deletion")
    except Exception:
        log.exception("ingest.remove failed")
        raise
    finally:
        _run(ingestor.aclose())

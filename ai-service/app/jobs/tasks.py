import os

from sqlalchemy import select

from app.core import logging
from app.core.celery_app import celery_app
from app.core.db_session import SyncSessionLocal
from app.core.enums import UploadStatus
from app.core.rag.pgvector import PGVectorWrapper
from app.db_models.upload import Upload

logger = logging.get_logger(__name__)


@celery_app.task
def add_upload(file_path: str, upload_id: int, user_id: int, chunk_size: int, chunk_overlap: int) -> None:
    with SyncSessionLocal() as session:
        statement = select(Upload).where(Upload.id == upload_id, Upload.is_deleted.is_(False))

        result = session.execute(statement)
        upload = result.scalar_one_or_none()

        if not upload:
            raise ValueError("Upload not found")
        try:
            PGVectorWrapper().add(file_path, upload_id, user_id, chunk_size, chunk_overlap)
            setattr(upload, "status", UploadStatus.COMPLETED)
            session.add(upload)
            session.commit()
            logger.info(f"Upload {upload_id} completed successfully")
        except Exception as e:
            logger.error(f"add_upload failed: {e}", exc_info=True)
            setattr(upload, "status", UploadStatus.FAILED)
            session.add(upload)
            session.commit()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


@celery_app.task
def edit_upload(file_path: str, upload_id: int, user_id: int, chunk_size: int, chunk_overlap: int) -> None:
    with SyncSessionLocal() as session:
        upload = session.get(Upload, upload_id)
        if not upload:
            raise ValueError("Upload not found")
        try:
            pgvector_store = PGVectorWrapper()
            logger.info("PGVectorWrapper initialized successfully")
            pgvector_store.update(file_path, upload_id, user_id, chunk_size, chunk_overlap)
            setattr(upload, "status", UploadStatus.COMPLETED)
            session.add(upload)
            session.commit()
            logger.info(f"Upload {upload_id} updated successfully")
        except Exception as e:
            logger.error(f"Error in edit_upload task: {e}", exc_info=True)
            setattr(upload, "status", UploadStatus.FAILED)
            session.add(upload)
            session.commit()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


@celery_app.task
def remove_upload(upload_id: int, user_id: int) -> None:
    with SyncSessionLocal() as session:
        upload = session.get(Upload, upload_id)
        if not upload:
            logger.warning(f"Upload not found in database for upload_id: {upload_id}, user_id: {user_id}")
            return

        try:
            pgvector_store = PGVectorWrapper()
            deletion_successful = pgvector_store.delete(upload_id, user_id)

            if deletion_successful:
                session.delete(upload)
                session.commit()
                logger.info(f"Upload {upload_id} removed from database and Qdrant successfully")
            else:
                logger.warning(f"Failed to delete documents from Qdrant for upload_id: {upload_id}, user_id: {user_id}")
                setattr(upload, "status", UploadStatus.FAILED)
                session.add(upload)
                session.commit()
        except Exception as e:
            logger.error(
                f"remove_upload failed for upload_id: {upload_id}, user_id: {user_id}. Error: {str(e)}",
                exc_info=True,
            )
            setattr(upload, "status", UploadStatus.FAILED)
            session.add(upload)
            session.commit()


@celery_app.task
def perform_search(
    user_id: int,
    upload_id: int,
    query: str,
    search_type: str,
    top_k: int,
    score_threshold: float,
):
    pgvector_store = PGVectorWrapper()
    if search_type == "vector":
        results = pgvector_store.vector_search(user_id, [upload_id], query, top_k, score_threshold)
    elif search_type == "fulltext":
        results = pgvector_store.fulltext_search(user_id, [upload_id], query, top_k, score_threshold)
    elif search_type == "hybrid":
        results = pgvector_store.hybrid_search(user_id, [upload_id], query, top_k, score_threshold)
    else:
        raise ValueError(f"Invalid search type: {search_type}")

    return [{"content": doc.page_content, "score": doc.metadata.get("score", 0)} for doc in results]

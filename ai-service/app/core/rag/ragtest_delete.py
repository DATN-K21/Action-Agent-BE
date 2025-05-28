import logging

from app.core.rag.pgvector import PGVectorWrapper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_delete_operation(user_id: int, upload_id: int):
    """Test delete operation for PGVectorWrapper"""
    pgvector_store = PGVectorWrapper()

    # 1. First, check the current document count
    logger.info("Checking initial document count:")
    initial_count = check_document_count(pgvector_store, user_id, upload_id)

    # 2. Execute delete operation
    logger.info(
        f"Attempting to delete documents for user_id: {user_id}, upload_id: {upload_id}"
    )
    deletion_result = pgvector_store.delete(upload_id, user_id)
    logger.info(f"Deletion result: {deletion_result}")

    # 3. Check document count again after deletion
    logger.info("Checking document count after deletion:")
    final_count = check_document_count(pgvector_store, user_id, upload_id)

    # 4. Compare results
    if initial_count > final_count:
        logger.info(f"Successfully deleted {initial_count - final_count} documents")
    elif initial_count == final_count:
        logger.warning("No documents were deleted")
    else:
        logger.error("Unexpected result: document count increased after deletion")


def check_document_count(
        pgvector_store: PGVectorWrapper, user_id: int, upload_id: int
) -> int:
    """Check document count using PGVectorWrapper's internal method"""
    count = pgvector_store._count_documents(user_id, upload_id)
    logger.info(
        f"Document count for user_id: {user_id}, upload_id: {upload_id}: {count}"
    )
    return count


def inspect_documents(pgvector_store: PGVectorWrapper, user_id: int, upload_id: int):
    """Inspect documents by performing a search to see what exists"""
    logger.info(f"Inspecting documents for user_id: {user_id}, upload_id: {upload_id}")

    # Use search method to get documents for inspection
    # Using empty query to get all documents matching the filter
    try:
        documents = pgvector_store.vector_store.similarity_search(
            query="",  # Empty query to get documents based on metadata filter
            k=10,
            filter={
                "user_id": user_id,
                "upload_id": upload_id
            }
        )

        logger.info(f"Found {len(documents)} documents:")
        for i, doc in enumerate(documents):
            logger.info(f"Document {i + 1}:")
            logger.info(f"Content preview: {doc.page_content[:100]}...")
            logger.info(f"Metadata: {doc.metadata}")
            logger.info("---")

    except Exception as e:
        logger.error(f"Error inspecting documents: {str(e)}")
        # Alternative: try to get some documents with a generic query
        try:
            documents = pgvector_store.search(user_id, [upload_id], "document")
            logger.info(f"Alternative search found {len(documents)} documents")
            for i, doc in enumerate(documents):
                logger.info(f"Document {i + 1} metadata: {doc.metadata}")
        except Exception as e2:
            logger.error(f"Alternative search also failed: {str(e2)}")


if __name__ == "__main__":
    user_id = 1  # Replace with actual user ID
    upload_id = 20  # Replace with actual upload ID

    pgvector_store = PGVectorWrapper()

    # Check collection information
    collection_info = pgvector_store.get_collection_info()
    logger.info(f"Collection info: {collection_info}")

    # Check and display documents
    inspect_documents(pgvector_store, user_id, upload_id)

    # Execute delete test
    test_delete_operation(user_id, upload_id)

    # Check documents again after deletion
    inspect_documents(pgvector_store, user_id, upload_id)

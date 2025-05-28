import json
import logging

from app.core.rag.pgvector import PGVectorWrapper
from app.core.tools.retriever_tool import create_retriever_tool_custom_modified

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_id = 1
upload_id = 5
query = "When was Thomson established?"  # Converted to English

# Create PGVectorWrapper instance
pgvector_store = PGVectorWrapper()

# Check collection information
collection_info = pgvector_store.get_collection_info()
logger.info(f"Collection info: {collection_info}")

# Check document content (alternative approach for PGVector)
logger.info("Checking document content:")
try:
    # Get some documents to inspect
    sample_docs = pgvector_store.vector_store.similarity_search("", k=10)
    for i, doc in enumerate(sample_docs):
        logger.info(f"Document {i + 1}:")
        logger.info(f"Content: {doc.page_content[:100]}...")
        logger.info(f"Metadata: {doc.metadata}")
        logger.info(f"user_id type: {type(doc.metadata.get('user_id'))}")
        logger.info(f"upload_id type: {type(doc.metadata.get('upload_id'))}")
        logger.info("---")
except Exception as e:
    logger.error(f"Error checking document content: {str(e)}")

# Execute search
search_results = pgvector_store.search(user_id, [upload_id], query)
logger.info(f"Search found {len(search_results)} documents")
for doc in search_results:
    logger.info(f"Content: {doc.page_content[:100]}...")
    logger.info(f"Metadata: {json.dumps(doc.metadata, ensure_ascii=False, indent=2)}")
    logger.info("---")

# Create and use retriever tool
retriever = pgvector_store.retriever(user_id, upload_id)
logger.info(f"Created retriever: {retriever}")
retriever_tool = create_retriever_tool_custom_modified(retriever)
logger.info(f"Created retriever tool: {retriever_tool}")

# Use retriever tool
result, docs = retriever_tool._run(query)

logger.info(f"Retriever tool result: {result[:100]}...")
# logger.info(f"Retriever tool found {len(docs)} documents")
# logger.info(f"Retriever search kwargs: {retriever.search_kwargs}")
# logger.info(f"Retriever vectorstore: {retriever.vectorstore}")

for doc in docs:
    logger.info(f"Retrieved document content: {doc.page_content[:100]}...")
    logger.info(
        f"Retrieved document metadata: {json.dumps(doc.metadata, ensure_ascii=False, indent=2)}"
    )
    logger.info("---")

# Execute unfiltered search
logger.info("Executing unfiltered search:")
unfiltered_results = pgvector_store.vector_store.similarity_search(query, k=5)
for doc in unfiltered_results:
    logger.info(f"Unfiltered Content: {doc.page_content[:100]}...")
    logger.info(
        f"Unfiltered Metadata: {json.dumps(doc.metadata, ensure_ascii=False, indent=2)}"
    )
    logger.info("---")

# Execute direct search without filters using similarity_search_with_score
logger.info("Executing direct search without filters:")
try:
    query_vector = pgvector_store.embedding_model.embed_query(query)
    # Use similarity_search_with_score to get more detailed results
    unfiltered_results_with_score = pgvector_store.vector_store.similarity_search_with_score(
        query, k=5
    )
    for doc, score in unfiltered_results_with_score:
        logger.info(f"Direct search result with score {score}: {doc.metadata}")
except Exception as e:
    logger.error(f"Error in direct search: {str(e)}")


def perform_native_pgvector_search(pgvector_store, user_id, upload_id, query):
    """Perform native PGVector search with filter using SQL"""
    logger.info("Performing native PGVector search with filter:")

    try:
        # Use the existing vector_search method which implements filtering
        native_results = pgvector_store.vector_search(
            user_id=user_id,
            upload_ids=[upload_id],
            query=query,
            top_k=5,
            score_threshold=0.0  # Set to 0 to get all results
        )

        logger.info(f"Native PGVector search found {len(native_results)} results")
        for i, doc in enumerate(native_results):
            logger.info(f"Native search result {i + 1}:")
            logger.info(f"Content: {doc.page_content[:100]}...")
            logger.info(f"Metadata: {doc.metadata}")
            logger.info(f"Score: {doc.metadata.get('score', 'N/A')}")
            logger.info("---")

        return native_results

    except Exception as e:
        logger.error(f"Error in native PGVector search: {str(e)}")
        return []


def perform_sql_based_search(pgvector_store, user_id, upload_id, query):
    """Perform SQL-based search directly on PGVector tables"""
    logger.info("Performing SQL-based search:")

    try:
        from sqlalchemy import text

        # Get query embedding
        query_vector = pgvector_store.embedding_model.embed_query(query)

        # Execute SQL query directly
        with pgvector_store.sync_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT document, cmetadata, 1 - (embedding <=> :query_vector) as similarity
                    FROM langchain_pg_embedding 
                    WHERE collection_id = (
                        SELECT uuid FROM langchain_pg_collection 
                        WHERE name = :collection_name
                    )
                    AND cmetadata->>'user_id' = :user_id 
                    AND cmetadata->>'upload_id' = :upload_id
                    ORDER BY embedding <=> :query_vector
                    LIMIT 5
                """),
                {
                    "collection_name": pgvector_store.collection_name,
                    "user_id": str(user_id),
                    "upload_id": str(upload_id),
                    "query_vector": str(query_vector)
                }
            )

            sql_results = result.fetchall()
            logger.info(f"SQL-based search found {len(sql_results)} results")

            for i, row in enumerate(sql_results):
                logger.info(f"SQL result {i + 1}:")
                logger.info(f"Document: {row.document[:100]}...")
                logger.info(f"Metadata: {row.cmetadata}")
                logger.info(f"Similarity: {row.similarity}")
                logger.info("---")

            return sql_results

    except Exception as e:
        logger.error(f"Error in SQL-based search: {str(e)}")
        return []


if __name__ == "__main__":
    # Execute native PGVector search
    native_results = perform_native_pgvector_search(
        pgvector_store, user_id, upload_id, query
    )

    # Execute SQL-based search for comparison
    sql_results = perform_sql_based_search(
        pgvector_store, user_id, upload_id, query
    )

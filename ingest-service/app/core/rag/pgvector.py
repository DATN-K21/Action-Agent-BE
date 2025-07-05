import logging
from collections.abc import Callable

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.rag.document_processor import load_and_split_document
from app.core.settings import env_settings

logger = logging.getLogger(__name__)


def _get_embedding_model() -> Embeddings:
    api_key = env_settings.OPENAI_API_KEY
    embedding_model = OpenAIEmbeddings(api_key=SecretStr(api_key))
    return embedding_model


class PGVectorWrapper:
    def __init__(self) -> None:
        self.collection_name = env_settings.PGVECTOR_COLLECTION
        self.connection_string = f"postgresql+psycopg2://{env_settings.PGVECTOR_POSTGRES_URL_PATH}"
        self.embedding_model = _get_embedding_model()
        self.sync_engine = create_engine(
            self.connection_string, connect_args={"options": f"-csearch_path={env_settings.PGVECTOR_POSTGRES_SCHEMA}"}
        )
        self.Session = sessionmaker(bind=self.sync_engine)
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        try:
            # Initialize PGVector store with schema-aware connection
            self.vector_store = PGVector(
                embeddings=self.embedding_model,
                collection_name=self.collection_name,
                connection=f"postgresql+psycopg2://{env_settings.PGVECTOR_POSTGRES_URL_PATH_WITH_SCHEMA}",
                use_jsonb=True,
            )

            logger.debug(f"PGVector store initialized with collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}", exc_info=True)
            raise

    def add(
        self,
        file_path_or_url: str,
        upload_id: str,
        user_id: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        callback: Callable[[], None] | None = None,
    ) -> None:
        try:
            docs = load_and_split_document(file_path_or_url, user_id, upload_id, chunk_size, chunk_overlap)
            # Ensure metadata is correctly set
            for doc in docs:
                doc.metadata["user_id"] = user_id
                doc.metadata["upload_id"] = upload_id

            # Count initial documents
            initial_count = self._count_documents(user_id, upload_id)

            # Add documents to vector store
            self.vector_store.add_documents(docs)

            # Count final documents
            final_count = self._count_documents(user_id, upload_id)
            added_count = final_count - initial_count

            logger.info(f"Added {added_count} documents for upload_id: {upload_id}, user_id: {user_id}")

            if callback:
                callback()
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            raise

    def delete(self, upload_id: str, user_id: str) -> bool:
        try:
            logger.debug(f"Attempting to delete documents for upload_id: {upload_id}, user_id: {user_id}")

            initial_count = self._count_documents(user_id, upload_id)
            logger.debug(f"Initial document count: {initial_count}")

            if initial_count == 0:
                logger.info(f"No documents found to delete for upload_id: {upload_id}, user_id: {user_id}")
                return True

            # Delete documents using SQL query
            with self.sync_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        DELETE FROM langchain_pg_embedding 
                        WHERE collection_id = (
                            SELECT uuid FROM langchain_pg_collection 
                            WHERE name = :collection_name
                        )
                        AND cmetadata->>'user_id' = :user_id 
                        AND cmetadata->>'upload_id' = :upload_id
                    """),
                    {"collection_name": self.collection_name, "user_id": str(user_id), "upload_id": str(upload_id)},
                )
                conn.commit()
                deleted_count = result.rowcount

            logger.info(
                f"Successfully deleted {deleted_count} documents for upload_id: {upload_id}, user_id: {user_id}"
            )
            return deleted_count > 0 or initial_count == 0

        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}", exc_info=True)
            return False

    def _count_documents(self, user_id: str, upload_id: str) -> int:
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM langchain_pg_embedding 
                        WHERE collection_id = (
                            SELECT uuid FROM langchain_pg_collection 
                            WHERE name = :collection_name
                        )
                        AND cmetadata->>'user_id' = :user_id 
                        AND cmetadata->>'upload_id' = :upload_id
                    """),
                    {"collection_name": self.collection_name, "user_id": str(user_id), "upload_id": str(upload_id)},
                )
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}", exc_info=True)
            return 0

    def vector_search(
        self, user_id: str, upload_ids: list[str], query: str, top_k: int = 4, score_threshold: float = 0.0
    ) -> list[Document]:
        try:
            # Create filter for metadata
            filter_dict = {"user_id": user_id, "upload_id": {"$in": upload_ids}}

            # Perform similarity search with filter
            documents = self.vector_store.similarity_search(query=query, k=top_k, filter=filter_dict)

            # Filter by score threshold if needed
            if score_threshold > 0.0:
                documents = [doc for doc in documents if doc.metadata.get("score", 1.0) >= score_threshold]

            return documents

        except Exception as e:
            logger.error(f"Error in vector_search: {str(e)}", exc_info=True)
            return []

    def fulltext_search(
        self, user_id: str, upload_ids: list[str], query: str, top_k: int = 4, score_threshold: float = 0.0
    ) -> list[Document]:
        # For now, fallback to vector search - can be enhanced with proper fulltext search
        return self.vector_search(user_id, upload_ids, query, top_k, score_threshold)

    def hybrid_search(
        self, user_id: str, upload_ids: list[str], query: str, top_k: int = 4, score_threshold: float = 0.0
    ) -> list[Document]:
        # For now, fallback to vector search - can be enhanced with proper hybrid search
        return self.vector_search(user_id, upload_ids, query, top_k, score_threshold)

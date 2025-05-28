import logging
import math
import re
from collections import Counter
from collections.abc import Callable

from langchain_core.documents import Document
from langchain_postgres import PGVector
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.rag.document_processor import load_and_split_document
from app.core.rag.embeddings import get_embedding_model
from app.core.settings import env_settings

logger = logging.getLogger(__name__)


class PGVectorWrapper:
    def __init__(self) -> None:
        self.collection_name = env_settings.PGVECTOR_COLLECTION  # Reusing the collection name setting
        self.connection_string = f"postgresql+psycopg2://{env_settings.POSTGRES_URL_PATH}"
        self.embedding_model = get_embedding_model(env_settings.EMBEDDING_PROVIDER)

        logger.debug(f"Initializing PGVector with connection: {self.connection_string}")

        # Create synchronous engine for initialization
        self.sync_engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.sync_engine)

        logger.debug("PGVector engine initialized successfully")

        self._initialize_vector_store()

    def _initialize_vector_store(self):
        try:
            # Initialize PGVector store
            self.vector_store = PGVector(
                embeddings=self.embedding_model,
                collection_name=self.collection_name,
                connection=self.connection_string,
                use_jsonb=True,
            )

            logger.debug(f"PGVector store initialized with collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}", exc_info=True)
            raise

    def add(
            self,
            file_path_or_url: str,
            upload_id: int,
            user_id: int,
            chunk_size: int = 500,
            chunk_overlap: int = 50,
            callback: Callable[[], None] | None = None,
    ) -> None:
        try:
            docs = load_and_split_document(
                file_path_or_url, user_id, upload_id, chunk_size, chunk_overlap
            )
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

            logger.info(
                f"Added {added_count} documents for upload_id: {upload_id}, user_id: {user_id}"
            )

            if callback:
                callback()
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            raise

    # noinspection SqlNoDataSourceInspection
    def delete(self, upload_id: int, user_id: int) -> bool:
        try:
            logger.debug(
                f"Attempting to delete documents for upload_id: {upload_id}, user_id: {user_id}"
            )

            initial_count = self._count_documents(user_id, upload_id)
            logger.debug(f"Initial document count: {initial_count}")

            if initial_count == 0:
                logger.info(
                    f"No documents found to delete for upload_id: {upload_id}, user_id: {user_id}"
                )
                return True

            # Delete documents using SQL query

            with self.sync_engine.connect() as conn:
                result = conn.execute(
                    text(f"""
                        DELETE FROM langchain_pg_embedding 
                        WHERE collection_id = (
                            SELECT uuid FROM langchain_pg_collection 
                            WHERE name = :collection_name
                        )
                        AND cmetadata->>'user_id' = :user_id 
                        AND cmetadata->>'upload_id' = :upload_id
                    """),
                    {
                        "collection_name": self.collection_name,
                        "user_id": str(user_id),
                        "upload_id": str(upload_id)
                    }
                )
                conn.commit()
                deleted_count = result.rowcount()

            logger.info(
                f"Successfully deleted {deleted_count} documents for upload_id: {upload_id}, user_id: {user_id}"
            )
            return deleted_count > 0 or initial_count == 0

        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}", exc_info=True)
            return False

    def update(
            self,
            file_path_or_url: str,
            upload_id: int,
            user_id: int,
            chunk_size: int = 500,
            chunk_overlap: int = 50,
            callback: Callable[[], None] | None = None,
    ) -> None:
        deletion_successful = self.delete(upload_id, user_id)
        if not deletion_successful:
            logger.warning(
                f"Failed to delete existing documents for upload_id: {upload_id}, user_id: {user_id}. Proceeding with add operation."
            )
        self.add(file_path_or_url, upload_id, user_id, chunk_size, chunk_overlap)
        if callback:
            callback()

    def search(self, user_id: int, upload_ids: list[int], query: str) -> list[Document]:
        try:
            # Create filter for metadata
            filter_dict = {
                "user_id": user_id,
                "upload_id": {"$in": upload_ids}
            }

            # Perform similarity search with filter
            documents = self.vector_store.similarity_search(
                query=query,
                k=4,
                filter=filter_dict
            )

            # Add score metadata (PGVector doesn't return scores by default in similarity_search)
            for doc in documents:
                if "score" not in doc.metadata:
                    doc.metadata["score"] = 1.0  # Default score

            return documents

        except Exception as e:
            logger.error(f"Error in search: {str(e)}", exc_info=True)
            return []

    def retriever(self, user_id: str, upload_id: str):
        logger.debug(
            f"Creating retriever for user_id: {user_id}, upload_id: {upload_id}"
        )

        filter_dict = {
            "user_id": user_id,
            "upload_id": upload_id
        }

        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": filter_dict, "k": 5},
            search_type="similarity",
        )
        logger.debug(f"Retriever created: {retriever}")
        return retriever

    def debug_retriever(self, user_id: int, upload_id: int, query: str):
        logger.debug(
            f"Debug retriever for user_id: {user_id}, upload_id: {upload_id}, query: '{query}'"
        )

        # Search with filter
        filtered_docs = self.search(user_id, [upload_id], query)
        logger.debug(f"Filtered search found {len(filtered_docs)} documents")
        for doc in filtered_docs:
            logger.debug(f"Filtered doc metadata: {doc.metadata}")

        # Search without filter
        unfiltered_docs = self.vector_store.similarity_search(query, k=5)
        logger.debug(f"Unfiltered search found {len(unfiltered_docs)} documents")

        # Print all document metadata
        for i, doc in enumerate(unfiltered_docs):
            logger.debug(f"Unfiltered doc {i} metadata: {doc.metadata}")

        return filtered_docs

    # noinspection SqlNoDataSourceInspection
    def get_collection_info(self):
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT c.name, c.uuid, COUNT(e.id) as document_count
                        FROM langchain_pg_collection c
                        LEFT JOIN langchain_pg_embedding e ON c.uuid = e.collection_id
                        WHERE c.name = :collection_name
                        GROUP BY c.name, c.uuid
                    """),
                    {"collection_name": self.collection_name}
                )
                collection_info = result.fetchone()
                logger.debug(f"Collection info: {collection_info}")
                return collection_info
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}", exc_info=True)
            return None

    def vector_search(
            self,
            user_id: int,
            upload_ids: list[int],
            query: str,
            top_k: int = 5,
            score_threshold: float = 0.5,
    ):
        try:
            filter_dict = {
                "user_id": user_id,
                "upload_id": {"$in": upload_ids}
            }

            # Use similarity_search_with_score to get scores
            search_results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter_dict
            )

            # Filter by score threshold and convert to documents
            filtered_results = []
            for doc, score in search_results:
                # Convert distance to similarity score (1 - distance for cosine)
                similarity_score = 1 - score if score <= 1 else 1 / (1 + score)
                if similarity_score >= score_threshold:
                    doc.metadata["score"] = similarity_score
                    filtered_results.append(doc)

            return filtered_results

        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}", exc_info=True)
            return []

    def fulltext_search(
            self,
            user_id: int,
            upload_ids: list[int],
            query: str,
            top_k: int = 5,
            score_threshold: float = 0.5,
    ):
        try:
            # Get all documents for the user and upload_ids
            filter_dict = {
                "user_id": user_id,
                "upload_id": {"$in": upload_ids}
            }

            # Get more documents for full-text processing
            all_docs = self.vector_store.similarity_search(
                query="",  # Empty query to get all matching metadata
                k=1000,
                filter=filter_dict
            )

            # Implement TF-IDF scoring
            query_terms = Counter(re.findall(r"\w+", query.lower()))
            filtered_results = []

            for doc in all_docs:
                content = doc.page_content.lower()
                content_terms = Counter(re.findall(r"\w+", content))

                # Calculate improved TF-IDF similarity score
                score = 0
                for term, query_count in query_terms.items():
                    if term in content_terms:
                        tf = content_terms[term] / len(content_terms)
                        idf = math.log(
                            len(all_docs)
                            / (
                                    sum(
                                        1
                                        for d in all_docs
                                        if term in d.page_content.lower()
                                    )
                                    + 1
                            )
                        )
                        score += (tf * idf) * query_count

                if score > 0:
                    filtered_results.append((doc, score))

            # Normalize scores
            if filtered_results:
                max_score = max(score for _, score in filtered_results)
                filtered_results = [
                    (doc, score / max_score) for doc, score in filtered_results
                ]

            # Apply score threshold
            filtered_results = [
                (doc, score)
                for doc, score in filtered_results
                if score >= score_threshold
            ]

            # Sort by score and take top_k
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            top_results = filtered_results[:top_k]

            # Add scores to document metadata
            result_docs = []
            for doc, score in top_results:
                doc.metadata["score"] = score
                result_docs.append(doc)

            return result_docs

        except Exception as e:
            logger.error(f"Error in fulltext search: {str(e)}", exc_info=True)
            return []

    def hybrid_search(
            self,
            user_id: int,
            upload_ids: list[int],
            query: str,
            top_k: int = 5,
            score_threshold: float = 0.5,
    ):
        vector_results = self.vector_search(
            user_id, upload_ids, query, top_k, score_threshold
        )
        fulltext_results = self.fulltext_search(
            user_id, upload_ids, query, top_k, score_threshold
        )

        # Combine results and sort by score
        combined_results = vector_results + fulltext_results
        combined_results.sort(key=lambda x: x.metadata["score"], reverse=True)
        return combined_results[:top_k]

    # noinspection SqlNoDataSourceInspection
    def _count_documents(self, user_id: int, upload_id: int) -> int:
        """Helper method to count documents for a specific user and upload"""
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(
                    text(f"""
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = (
                            SELECT uuid FROM langchain_pg_collection 
                            WHERE name = :collection_name
                        )
                        AND cmetadata->>'user_id' = :user_id 
                        AND cmetadata->>'upload_id' = :upload_id
                    """),
                    {
                        "collection_name": self.collection_name,
                        "user_id": str(user_id),
                        "upload_id": str(upload_id)
                    }
                )
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}", exc_info=True)
            return 0

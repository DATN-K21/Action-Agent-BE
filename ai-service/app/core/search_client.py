"""
Search client for ai-service to communicate with retrieval-service via gRPC.
"""

import asyncio
import time
from typing import List

import grpc
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class SearchError(Exception):
    """Custom exception for search-related errors."""

    pass


class SearchTimeoutError(SearchError):
    """Raised when search operation times out."""

    pass


class SearchConnectionError(SearchError):
    """Raised when gRPC connection fails."""

    pass


class SearchAPIRetriever(BaseRetriever):
    """Enhanced retriever that uses the search API with support for multiple uploads."""

    user_id: str = Field(description="User ID for the search")
    upload_ids: List[str] = Field(default_factory=list, description="List of upload IDs for batch search")
    top_k: int = Field(default=5, description="Number of results to return")
    score_threshold: float = Field(default=0.5, description="Minimum score threshold")
    timeout: float = Field(default=30.0, description="gRPC call timeout in seconds")
    max_workers: int = Field(default=5, description="Max concurrent workers for batch search")

    def __init__(self, **data):
        """Initialize retriever with validation."""
        super().__init__(**data)

        if not self.upload_ids:
            raise ValueError("Either upload_id or upload_ids must be provided")

        # Validate search parameters
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0")

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Retrieve documents using the retrieval service gRPC API."""
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        upload_ids = self.upload_ids
        if not upload_ids:
            logger.warning("No upload_ids provided for search")
            return []

        if not isinstance(upload_ids, list):
            raise ValueError("upload_ids must be a list of strings")

        try:
            start_time = time.time()

            # Import gRPC generated files
            from generated import retrieval_pb2, retrieval_pb2_grpc

            # Create gRPC channel with timeout
            channel_options = [
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 5000),
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_time_between_pings_ms", 10000),
                ("grpc.http2.min_ping_interval_without_data_ms", 300000),
            ]

            with grpc.insecure_channel(env_settings.RETRIEVAL_SERVICE_GRPC_URL, options=channel_options) as channel:
                stub = retrieval_pb2_grpc.RetrievalServiceStub(channel)

                # Create request
                request = retrieval_pb2.SearchRequest(  # type: ignore
                    user_id=self.user_id,
                    upload_ids=upload_ids,
                    query=query,
                    top_k=self.top_k,
                    score_threshold=self.score_threshold,
                )

                # Make gRPC call with timeout
                try:
                    response = stub.Search(request, timeout=self.timeout)
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                        raise SearchTimeoutError(f"Search timeout after {self.timeout}s")
                    elif e.code() == grpc.StatusCode.UNAVAILABLE:
                        raise SearchConnectionError(f"Retrieval service unavailable: {e.details()}")
                    else:
                        raise SearchError(f"gRPC error: {e.code()} - {e.details()}")

            # Convert gRPC response to Document objects
            documents = []
            for result in response.results:
                metadata = dict(result.metadata)
                metadata["score"] = result.score
                metadata["upload_ids"] = upload_ids  # Ensure upload_id is in metadata
                documents.append(Document(page_content=result.content, metadata=metadata))

            elapsed_time = time.time() - start_time
            logger.info(f"Retrieved {len(documents)} documents for upload {upload_ids} in {elapsed_time:.2f}s (query: {query[:50]}...)")
            return documents

        except (SearchError, SearchTimeoutError, SearchConnectionError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in gRPC search for upload {upload_ids}: {e}", exc_info=True)
            raise SearchError(f"Search failed for upload {upload_ids}: {str(e)}")

    async def _aget_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Async version with proper async gRPC implementation."""
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        # For now, run in thread pool - could be enhanced with async gRPC later
        return await asyncio.get_event_loop().run_in_executor(None, self._get_relevant_documents, query, **kwargs)


class SearchAPIWrapper:
    """Enhanced wrapper that provides improved interface to retrieval service via gRPC."""

    def __init__(self, timeout: float = 30.0, max_workers: int = 5):
        """Initialize wrapper with configuration."""
        self.timeout = timeout
        self.max_workers = max_workers

    def retriever(self, user_id: str, upload_ids: List[str], **kwargs) -> SearchAPIRetriever:
        """Create a retriever for single or multiple uploads.

        Args:
            user_id: User ID for the search
            upload_ids: List of upload IDs for batch search
            **kwargs: Additional search parameters

        Returns:
            SearchAPIRetriever instance
        """
        if not upload_ids:
            raise ValueError("upload_ids must be provided")

        return SearchAPIRetriever(
            user_id=user_id,
            upload_ids=upload_ids,
            timeout=self.timeout,
            max_workers=self.max_workers,
            **kwargs,
        )

    async def asearch(
        self,
        user_id: str,
        upload_ids: List[str],
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Document]:
        """Async direct search method for convenience.

        Args:
            user_id: User ID for the search
            upload_ids: List of upload IDs to search
            query: Search query
            search_type: Type of search (vector, fulltext, hybrid)
            top_k: Number of results to return
            score_threshold: Minimum score threshold

        Returns:
            List of Document objects
        """
        retriever = self.retriever(
            user_id=user_id,
            upload_ids=upload_ids,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return await retriever._aget_relevant_documents(query)

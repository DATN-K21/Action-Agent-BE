"""
Fast and compact search client for ai-service to communicate with retrieval-service via gRPC.

Features:
- Native async gRPC with connection pooling
- Simple retry logic and timeout management

Usage:
    # Basic search
    client = APIRetriever("user123", ["upload1", "upload2"])
    results = await client.search("query")

    # With context manager
    async with RetrieverContext(client) as search_client:
        results = await search_client.search("query")
"""

import asyncio
import time
from typing import List

import grpc.aio
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from app.core import logging
from app.core.grpc_pool import close_grpc_connections, get_grpc_channel
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class SearchError(Exception):
    """Search operation failed."""

    pass


class APIRetriever(BaseRetriever):
    """Fast, compact search client with async gRPC and connection pooling."""

    user_id: str = Field(description="User ID for the search")
    upload_ids: List[str] = Field(default_factory=list, description="List of upload IDs for search")
    top_k: int = Field(default=5, description="Number of results to return")
    score_threshold: float = Field(default=0.5, description="Minimum score threshold")
    timeout: float = Field(default=30.0, description="gRPC call timeout in seconds")

    def __init__(
        self,
        user_id: str,
        upload_ids: List[str],
        top_k: int = 5,
        score_threshold: float = 0.5,
        timeout: float = 30.0,
        **kwargs,
    ):
        """Initialize search client with validation."""
        super().__init__(**kwargs)
        self.user_id = user_id
        self.upload_ids = upload_ids or []
        self.top_k = max(1, top_k)
        self.score_threshold = max(0.0, min(1.0, score_threshold))
        self.timeout = max(1.0, timeout)

        if not user_id or not upload_ids:
            raise ValueError("user_id and upload_ids must be provided")
        if not env_settings.RETRIEVAL_SERVICE_GRPC_URL:
            raise ValueError("RETRIEVAL_SERVICE_GRPC_URL must be set")

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Sync method - runs async version in event loop."""
        return asyncio.run(self._aget_relevant_documents(query))

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Main async search method."""
        return await self.search(query)

    async def search(self, query: str, max_retries: int = 2) -> List[Document]:
        """Perform search with automatic retry."""
        if not query.strip():
            return []

        for attempt in range(max_retries + 1):
            try:
                return await self._perform_search(query)
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Search failed after {max_retries + 1} attempts: {e}")
                    return []
                await asyncio.sleep(0.5 * (attempt + 1))  # Simple backoff

        return []  # Explicit return for type safety

    async def _perform_search(self, query: str) -> List[Document]:
        """Perform the actual gRPC search."""
        start_time = time.time()

        try:
            from generated import retrieval_pb2, retrieval_pb2_grpc

            # Get channel from pool with optimized options
            channel_options = [
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 5000),
                ("grpc.max_receive_message_length", 4 * 1024 * 1024),
                ("grpc.max_send_message_length", 4 * 1024 * 1024),
            ]

            channel = await get_grpc_channel(env_settings.RETRIEVAL_SERVICE_GRPC_URL, channel_options)
            stub = retrieval_pb2_grpc.RetrievalServiceStub(channel)

            # Create and send request
            request = retrieval_pb2.SearchRequest(  # type: ignore
                user_id=self.user_id,
                upload_ids=self.upload_ids,
                query=query,
                top_k=self.top_k,
                score_threshold=self.score_threshold,
            )

            response = await asyncio.wait_for(stub.Search(request), timeout=self.timeout)

            # Convert to documents
            documents = []
            for result in response.results:
                metadata = dict(result.metadata)
                metadata.update({"score": result.score, "upload_ids": self.upload_ids})
                documents.append(Document(page_content=result.content, metadata=metadata))

            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(documents)} documents in {elapsed:.2f}s")
            return documents

        except asyncio.TimeoutError:
            raise SearchError(f"Search timeout after {self.timeout}s")
        except grpc.aio.AioRpcError as e:
            raise SearchError(f"gRPC error: {e.code()} - {e.details()}")

    async def close(self):
        """Close connections (for compatibility)."""
        await close_grpc_connections()


# Context manager for automatic cleanup
class RetrieverContext:
    """Context manager for search operations with automatic cleanup."""

    def __init__(self, client: APIRetriever):
        self.client = client

    async def __aenter__(self) -> APIRetriever:
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()


# Simple factory function
def create_search_client(user_id: str, upload_ids: List[str], **kwargs) -> APIRetriever:
    """Create a configured search client."""
    return APIRetriever(user_id=user_id, upload_ids=upload_ids, **kwargs)

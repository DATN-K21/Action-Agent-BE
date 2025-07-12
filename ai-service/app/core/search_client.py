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


class CustomRetriever(BaseRetriever):
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        Synchronous wrapper for _aget_relevant_documents. Runs the async method safely in sync context.
        Avoids asyncio.run() if an event loop is already running (e.g., in FastAPI).
        """
        logger.info(f"[SYNC] _get_relevant_documents called with query: {query}")
        if not query.strip():
            return []

        MAX_RETRIES = 2
        async def _run():
            for attempt in range(MAX_RETRIES):
                try:
                    if not self.upload_id:
                        logger.warning("No upload_id provided, skipping search.")
                        return []
                    return await self._aget_relevant_documents(query)
                except SearchError:
                    raise
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        logger.error(f"Search failed after {MAX_RETRIES} attempts: {e}")
                        return []
                    await asyncio.sleep(0.5 * (attempt + 1))
            return []

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already in an event loop, run the async code in a separate thread
            import concurrent.futures
            def runner():
                return asyncio.run(_run())
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(runner)
                return future.result()
        else:
            return asyncio.run(_run())
    """Fast, compact search client with async gRPC and connection pooling."""

    user_id: str = Field(description="User ID for the search")
    upload_id: str = Field(description="Upload ID for the search context")
    top_k: int = Field(default=5, description="Number of top results to return")
    score_threshold: float = Field(default=0.5, description="Minimum score to include a result")

    def __init__(self, **data):
        """Initialize search client with validation."""
        # Extract our custom fields
        user_id = data.get("user_id")
        upload_id = data.get("upload_id")

        if not user_id or not upload_id:
            raise ValueError("user_id and upload_id must be provided")
        if not env_settings.RETRIEVAL_SERVICE_GRPC_URL:
            raise ValueError("RETRIEVAL_SERVICE_GRPC_URL must be set")

        # Validate and set defaults for our custom fields
        data["top_k"] = max(1, data.get("top_k", 5))
        data["score_threshold"] = max(0.0, min(1.0, data.get("score_threshold", 0.5)))

        # Initialize the parent Pydantic model
        super().__init__(**data)

    @classmethod
    def create(
        cls,
        user_id: str,
        upload_id: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        **kwargs,
    ) -> "CustomRetriever":
        """Create a new CustomRetriever instance with proper validation."""
        return cls(user_id=user_id, upload_id=upload_id, top_k=top_k, score_threshold=score_threshold, **kwargs)

    # Removed deprecated synchronous _get_relevant_documents method to enforce async-only usage

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Main async search method."""
        logger.info(f"[ASYNC] _aget_relevant_documents called with query: {query}")
        if not query.strip():
            return []

        MAX_RETRIES = 2
        for attempt in range(MAX_RETRIES):
            try:
                if not self.upload_id:
                    logger.warning("No upload_id provided, skipping search.")
                    return []
                return await self._perform_search(query, self.upload_id)
            except SearchError:
                # SearchError is already properly handled, re-raise it
                raise
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Search failed after {MAX_RETRIES} attempts: {e}")
                    return []
                await asyncio.sleep(0.5 * (attempt + 1))  # Simple backoff

        return []  # Explicit return for type safety

    async def _perform_search(self, query: str, upload_id: str) -> List[Document]:
        """Perform the actual gRPC search."""
        start_time = time.time()

        try:
            from generated import retrieval_pb2, retrieval_pb2_grpc

            # Get channel from pool with optimized options
            channel_options = [
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 5000),
                ("grpc.max_receive_message_length", 16 * 1024 * 1024),  # 16MB
                ("grpc.max_send_message_length", 16 * 1024 * 1024),  # 16MB
            ]

            channel = await get_grpc_channel(env_settings.RETRIEVAL_SERVICE_GRPC_URL, channel_options)
            stub = retrieval_pb2_grpc.RetrievalServiceStub(channel)

            # Create and send request
            request = retrieval_pb2.SearchRequest(  # type: ignore
                user_id=self.user_id,
                upload_id=upload_id,
                query=query,
                top_k=self.top_k,
                score_threshold=self.score_threshold,
            )

            TIMEOUT_SECONDS = 30.0  # Timeout for gRPC call

            # Make the gRPC call
            response = await stub.Search(request, timeout=TIMEOUT_SECONDS)

            # Convert to documents
            documents = []
            for result in response.results:
                metadata = dict(result.metadata)
                metadata.update({"score": result.score, "upload_id": upload_id})
                documents.append(Document(page_content=result.content, metadata=metadata))

            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(documents)} documents in {elapsed:.2f}s")
            return documents

        except grpc.aio.AioRpcError as e:
            raise SearchError(f"gRPC error: {e.code()} - {e.details()}")
        except Exception as e:
            raise SearchError(f"Search error: {e}")

    async def close(self):
        """Close connections (for compatibility)."""
        await close_grpc_connections()


# Simple factory function
def create_search_client(user_id: str, upload_id: str) -> CustomRetriever:
    """Create a new search client instance."""
    return CustomRetriever.create(user_id=user_id, upload_id=upload_id, top_k=5, score_threshold=0.5)

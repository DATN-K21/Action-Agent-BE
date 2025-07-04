"""
Search client for ai-service to replace direct vector store access.
Uses the search API to communicate with ingest-service.
"""

import asyncio
from typing import Any, List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from app.celery import celery_app
from app.core import logging

logger = logging.get_logger(__name__)


class SearchAPIRetriever(BaseRetriever):
    """Retriever that uses the search API instead of direct vector store access."""

    user_id: str = Field(description="User ID for the search")
    upload_id: str = Field(description="Upload ID for the search")
    search_type: str = Field(default="vector", description="Type of search to perform")
    top_k: int = Field(default=5, description="Number of results to return")
    score_threshold: float = Field(default=0.5, description="Minimum score threshold")

    def _get_relevant_documents(self, query: str, **kwargs: Any) -> List[Document]:
        """Retrieve documents using the search API."""
        try:
            # Send search task to ingest-service
            task = celery_app.send_task(
                "ingest.document.search",
                args=[self.user_id, self.upload_id, query, self.search_type, self.top_k, self.score_threshold],
                queue="document.search",
            )

            # Wait for result with timeout
            result = task.get(timeout=30)

            # Convert result to Document objects
            documents = []
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        content = item.get("content", str(item))
                        metadata = item.get("metadata", {})
                        documents.append(Document(page_content=content, metadata=metadata))
                    else:
                        documents.append(Document(page_content=str(item)))

            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def _aget_relevant_documents(self, query: str, **kwargs: Any) -> List[Document]:
        """Async version - runs sync version in thread pool."""
        return await asyncio.get_event_loop().run_in_executor(None, self._get_relevant_documents, query, **kwargs)


class SearchAPIWrapper:
    """Wrapper that provides similar interface to PGVectorWrapper but uses search API."""

    def retriever(self, user_id: str, upload_id: str, **kwargs) -> SearchAPIRetriever:
        """Create a retriever for the given user and upload."""
        return SearchAPIRetriever(user_id=user_id, upload_id=upload_id, **kwargs)

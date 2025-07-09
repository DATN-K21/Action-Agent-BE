from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from pydantic import SecretStr
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from app.core import logging as log_mod
from app.core.document_processor import aload_and_split_document
from app.core.settings import env_settings

log = log_mod.get_logger(__name__)

# ── cfg
COLLECTION = env_settings.QDRANT_COLLECTION
CLIENT = QdrantClient(url=env_settings.QDRANT_URL, api_key=env_settings.QDRANT_API_KEY, prefer_grpc=True)

DENSE_EMB = OpenAIEmbeddings(model=env_settings.OPENAI_EMBED_MODEL, api_key=SecretStr(env_settings.OPENAI_API_KEY))
SPARSE_EMB = FastEmbedSparse(model_name="Qdrant/bm42-all-minilm-l6-v2-attentions")

POOL = ThreadPoolExecutor(max_workers=4)


# ── helper to off-load sync work
async def _run(fn, *a, **kw):
    return await asyncio.get_running_loop().run_in_executor(POOL, lambda: fn(*a, **kw))


async def create_collection_if_not_exists(collection_name: str | None = None) -> bool:
    """
    Creates a Qdrant collection with hybrid (dense + sparse) vector configuration if it doesn't exist.
    """
    if collection_name is None:
        collection_name = COLLECTION

    try:
        # Check if collection already exists
        collections = await _run(CLIENT.get_collections)
        existing_collections = [col.name for col in collections.collections]

        if collection_name in existing_collections:
            log.info(f"Collection '{collection_name}' already exists")
            return True

        log.info(f"Creating collection '{collection_name}' with hybrid vector configuration")

        # Get embedding dimensions for dense vectors
        dense_vector = await _run(DENSE_EMB.embed_query, "sample text")
        dense_dim = len(dense_vector)

        # Create collection with both dense and sparse vector configurations
        await _run(
            CLIENT.create_collection,
            collection_name=collection_name,
            vectors_config={
                "dense": rest.VectorParams(
                    size=dense_dim,
                    distance=rest.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": rest.SparseVectorParams(
                    index=rest.SparseIndexParams(
                        on_disk=False,
                    )
                ),
            },
        )

        log.info(f"Successfully created collection '{collection_name}' with dense_dim={dense_dim}")
        return True

    except Exception as e:
        log.error(f"Failed to create collection '{collection_name}': {e}")
        return False


class LCQdrantIngestor:
    """Async façade around LangChain Qdrant HYBRID store."""

    def __init__(self) -> None:
        self._vs: QdrantVectorStore | None = None

    def _vs_lazy(self) -> QdrantVectorStore:
        if self._vs is None:
            self._vs = QdrantVectorStore(
                client=CLIENT,
                collection_name=COLLECTION,
                embedding=DENSE_EMB,
                sparse_embedding=SPARSE_EMB,
                retrieval_mode=RetrievalMode.HYBRID,
                vector_name="dense",
                sparse_vector_name="sparse",
            )
        return self._vs

    # ───────────────── ingest
    async def add_upload(
        self, blob_url: str, upload_id: str, user_id: str, *, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> int:
        # Ensure collection exists before ingesting
        await create_collection_if_not_exists()

        docs: List[Document] = await aload_and_split_document(
            blob_url, user_id, upload_id, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        if not docs:
            raise ValueError("File produced 0 chunks")

        await _run(self._vs_lazy().add_documents, docs)
        log.info("Ingested %s chunks (dense+SPLADE) upload=%s user=%s", len(docs), upload_id, user_id)
        return len(docs)

    # ───────────────── delete
    async def delete_upload(self, upload_id: str, user_id: str) -> bool:
        filt = rest.Filter(
            must=[
                rest.FieldCondition(key="user_id", match=rest.MatchValue(value=user_id)),
                rest.FieldCondition(key="upload_id", match=rest.MatchValue(value=upload_id)),
            ]
        )
        await _run(self._vs_lazy().delete, filter=filt)
        log.info("Deleted upload=%s user=%s", upload_id, user_id)
        return True

    # ───────────────── context mgmt
    async def aclose(self):
        POOL.shutdown(wait=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()

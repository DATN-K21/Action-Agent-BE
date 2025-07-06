"""
QdrantIngestor - streaming uploader for RAG chunks
──────────────────────────────────────────────────
• Batches + parallel-embeds chunks, then uploads with a single
  `AsyncQdrantClient.upload_collection()` call → 1 round-trip.
• Payload carries `user_id`, `upload_id`, original source/page etc.
• Companion `delete_upload()` removes every point that belongs to
  (user_id, upload_id) via filtered `delete()` - no hard-coded IDs.
"""

from __future__ import annotations

import logging
import uuid

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from app.core.document_processor import aload_and_split_document
from app.core.settings import env_settings

# ───────────────────────── config ─────────────────────────
QDRANT_URL = env_settings.QDRANT_URL
QDRANT_API_KEY = env_settings.QDRANT_API_KEY
QDRANT_COLLECTION = env_settings.QDRANT_COLLECTION
OPENAI_EMBED_MODEL = env_settings.OPENAI_EMBED_MODEL
OPENAI_API_KEY = env_settings.OPENAI_API_KEY

QDRANT_MERGE_THRESHOLD = 128  # Qdrant merge-threshold
MAX_WORKERS = 4  # parallel embed threads
EMBEDDING_CACHE = 4096  # LRU

logger = logging.getLogger(__name__)
_emb = OpenAIEmbeddings(model=OPENAI_EMBED_MODEL, api_key=SecretStr(OPENAI_API_KEY))


# ───────────────────────── main class ─────────────────────
class QdrantIngestor:
    def __init__(self) -> None:
        self.cli = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # ------------- private helpers ------------------------
    async def _ensure_collection_exists(self) -> None:
        """Ensure the collection exists, create if it doesn't."""
        try:
            # Check if collection exists
            await self.cli.get_collection(QDRANT_COLLECTION)
        except Exception:
            # Collection doesn't exist, create it
            logger.info("Creating Qdrant collection: %s", QDRANT_COLLECTION)
            await self.cli.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=rest.VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=rest.Distance.COSINE,
                ),
                optimizers_config=rest.OptimizersConfigDiff(
                    default_segment_number=2,
                ),
                hnsw_config=rest.HnswConfigDiff(
                    payload_m=16,
                    m=0,
                ),
            )

    # ------------- public API -----------------------------
    async def add_upload(
        self,
        blob_url: str,
        upload_id: str,
        user_id: str,
        *,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> int:
        """Download + split file, embed chunks, upload to Qdrant."""
        # 1. Split to Document chunks
        docs: list[Document] = await aload_and_split_document(
            blob_url,
            user_id,
            upload_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # 2. Embed in parallel batches
        vectors: list[list[float]] = []
        for i in range(0, len(docs), QDRANT_MERGE_THRESHOLD):
            batch = docs[i : i + QDRANT_MERGE_THRESHOLD]
            vecs = await _emb.aembed_documents(list([d.page_content for d in batch]))
            vectors.extend(vecs)

        # 3. Build points
        points = [
            rest.PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    **doc.metadata,
                    "content": doc.page_content,
                    "chunk_idx": idx,
                },
            )
            for idx, (doc, vec) in enumerate(zip(docs, vectors))
        ]

        # 4. Ensure collection exists before uploading
        await self._ensure_collection_exists()

        # 5. Upload points to Qdrant
        await self.cli.upsert(
            collection_name=QDRANT_COLLECTION,
            wait=True,
            points=points,
        )

        logger.info(
            "Ingested %s chunks for upload_id=%s user_id=%s → collection=%s",
            len(points),
            upload_id,
            user_id,
            QDRANT_COLLECTION,
        )
        return len(points)

    async def delete_upload(self, upload_id: str, user_id: str) -> int:
        """Delete all chunks belonging to (user_id, upload_id)."""
        # Ensure collection exists before trying to delete
        await self._ensure_collection_exists()

        res = await self.cli.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[
                        rest.FieldCondition(key="user_id", match=rest.MatchValue(value=user_id)),
                        rest.FieldCondition(key="upload_id", match=rest.MatchValue(value=upload_id)),
                    ]
                )
            ),
        )
        deleted = res.status == "completed"
        logger.info(
            "Removed upload_id=%s user_id=%s (success=%s)",
            upload_id,
            user_id,
            deleted,
        )
        return deleted

    async def aclose(self):
        await self.cli.close()

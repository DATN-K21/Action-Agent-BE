"""
QdrantStore - retrieval-only
────────────────────────────
requirements:
    qdrant-client >= 1.14
    openai          >= 1.2
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny, MatchText, MatchValue

from app.core import logging
from app.core.settings import env_settings

log = logging.get_logger(__name__)

# ────────── shared embed pool (OpenAI calls are blocking) ────────────────────
_OPENAI = OpenAI(api_key=env_settings.OPENAI_API_KEY)
_EMB_POOL = ThreadPoolExecutor(max_workers=4)


async def _embed(text: str) -> list[float]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _EMB_POOL,
        lambda: _OPENAI.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding,
    )


# ────────── Qdrant retrieval wrapper ─────────────────────────────────────────
class QdrantStore:
    """Stateless helper – create once per service process."""

    def __init__(self) -> None:
        self._cli = AsyncQdrantClient(
            url=env_settings.QDRANT_URL,  # e.g. http://qdrant:6333
            api_key=env_settings.QDRANT_API_KEY or None,
            timeout=5,
        )
        self._col = env_settings.QDRANT_COLLECTION
        log.info("QdrantStore ready", collection=self._col)

    # --------------------------------------------------------------------- #
    # helpers
    # --------------------------------------------------------------------- #
    def _filter(self, user_id: str, uploads: list[str]) -> Filter:
        return Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                FieldCondition(key="upload_id", match=MatchAny(any=uploads)),
            ]
        )

    # --------------------------------------------------------------------- #
    # vector search (ANN)
    # --------------------------------------------------------------------- #
    async def vector_search(
        self,
        user_id: str,
        upload_ids: list[str],
        query: str,
        top_k: int = 8,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        vec = await _embed(query)
        pts = await self._cli.search(
            collection_name=self._col,
            query_vector=vec,
            query_filter=self._filter(user_id, upload_ids),
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold or None,
        )
        return [{"content": p.payload["content"], "metadata": p.payload} for p in pts]

    # --------------------------------------------------------------------- #
    # full-text  (payload match_text)
    # --------------------------------------------------------------------- #
    async def fulltext_search(
        self,
        user_id: str,
        upload_ids: list[str],
        query: str,
        top_k: int = 8,
    ) -> list[dict]:
        filt = self._filter(user_id, upload_ids)
        filt.must.append(FieldCondition(key="content", match=MatchText(text=query)))

        pts, _ = await self._cli.scroll(
            collection_name=self._col,
            filter=filt,
            limit=top_k * 5,  # wider slice, then trim
            with_payload=True,
        )
        return [{"content": p.payload["content"], "metadata": p.payload} for p in pts[:top_k]]

    # --------------------------------------------------------------------- #
    # hybrid  (vector + keyword rank-fusion)
    # --------------------------------------------------------------------- #
    async def hybrid_search(
        self,
        user_id: str,
        upload_ids: list[str],
        query: str,
        top_k: int = 8,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        vec = await _embed(query)
        pts = await self._cli.search(
            collection_name=self._col,
            query_vector=vec,
            keyword=query,  # enables fusion
            filter=self._filter(user_id, upload_ids),
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold or None,
        )
        return [{"content": p.payload["content"], "metadata": p.payload} for p in pts]

    # --------------------------------------------------------------------- #
    async def close(self) -> None:
        await self._cli.close()
        _EMB_POOL.shutdown(wait=False)
        log.info("QdrantStore closed")

    # --------------------------------------------------------------------- #
    # public dispatcher – choose mode
    # --------------------------------------------------------------------- #
    async def search(
        self,
        user_id: str,
        upload_ids: list[str],
        query: str,
        top_k: int = 8,
        score_threshold: float = 0.0,
        mode: str = "vector",  # "", "vector", "fulltext", "hybrid"
    ) -> list[dict]:
        router = {
            "": self.vector_search,
            "vector": self.vector_search,
            "fulltext": self.fulltext_search,
            "hybrid": self.hybrid_search,
        }.get(mode, self.vector_search)

        return await router(user_id, upload_ids, query, top_k, score_threshold)

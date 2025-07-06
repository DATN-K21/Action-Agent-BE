"""
Async Qdrant backend
────────────────────
• vector_search   - ANN only
• fulltext_search - payload text index
• hybrid_search   - vector + keyword rank-fusion
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from pydantic import SecretStr
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny, MatchText, MatchValue

from app.core import logging
from app.core.settings import env_settings

log = logging.get_logger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Shared embedding pool (OpenAI is blocking)
# ────────────────────────────────────────────────────────────────────────────
_EMBED_POOL = ThreadPoolExecutor(max_workers=4)
_embeddings = OpenAIEmbeddings(api_key=SecretStr(env_settings.OPENAI_API_KEY))


async def _embed(text: str) -> list[float]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EMBED_POOL, _embeddings.embed_query, text)


# ────────────────────────────────────────────────────────────────────────────
# Qdrant store wrapper
# ────────────────────────────────────────────────────────────────────────────
class QdrantStore:
    """One instance per process; methods are async."""

    def __init__(self) -> None:
        self._client = AsyncQdrantClient(
            url=env_settings.QDRANT_URL,  # e.g. "http://localhost:6333"
            api_key=getattr(env_settings, "QDRANT_API_KEY", None),
            timeout=5,
        )
        self._col = env_settings.QDRANT_COLLECTION
        self._vs = Qdrant(
            client=self._client,
            collection_name=self._col,
            embeddings=_embeddings,  # only for upserts
        )
        log.info("QdrantStore ready", collection=self._col)

    # ---------------------------- retrieval modes --------------------------- #
    async def _vector(self, uid: str, uploads: list[str], query: str, k: int, thr: float) -> list[Document]:
        vec = await _embed(query)
        docs_scores = await asyncio.to_thread(
            self._vs.similarity_search_with_score,
            query=query,
            k=k,
            filter={"user_id": uid, "upload_id": {"$in": uploads}},
            score_threshold=thr or None,
            embedding=vec,
        )
        return [d for d, _ in docs_scores]

    async def _fulltext(self, uid: str, uploads: list[str], query: str, k: int, *_):
        filt = Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=uid)),
                FieldCondition(key="upload_id", match=MatchAny(any=uploads)),
                FieldCondition(key="content", match=MatchText(text=query)),
            ]
        )
        points, _ = await self._client.scroll(
            collection_name=self._col,
            filter=filt,
            limit=k * 5,  # get a wider slice
            with_payload=True,
        )
        return [
            Document(p.payload["content"], p.payload)  # type: ignore
            for p in points[:k]  # naive cut-off
        ]

    async def _hybrid(self, uid: str, uploads: list[str], query: str, k: int, thr: float):
        vec = await _embed(query)
        filt = Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=uid)),
                FieldCondition(key="upload_id", match=MatchAny(any=uploads)),
            ]
        )
        points = await self._client.search(
            collection_name=self._col,
            query_vector=vec,
            keyword=query,  # hybrid fusion
            filter=filt,
            limit=k,
            with_payload=True,
            score_threshold=thr or None,
        )
        return [Document(p.payload["content"], p.payload) for p in points]  # type: ignore

    # ---------------------------- public facade ---------------------------- #
    async def search(
        self,
        user_id: str,
        upload_ids: list[str],
        query: str,
        top_k: int,
        score_thr: float,
        mode: str,
    ) -> list[Document]:
        router = {
            "vector": self._vector,
            "fulltext": self._fulltext,
            "hybrid": self._hybrid,
        }.get(mode, self._vector)
        return await router(user_id, upload_ids, query, top_k, score_thr)

    # ---------------------------- cleanup ----------------------------------- #
    async def close(self) -> None:
        await self._client.close()
        _EMBED_POOL.shutdown(wait=False)
        log.info("Qdrant client closed")

# qdrant_store.py
"""
High-performance hybrid retriever for RAG
────────────────────────────────────────
• Dense + sparse RRF fusion runs **inside Qdrant** ➜ one network hop
• Batched & memoised OpenAI embeddings ➜ low latency + cost
• Optional LLM re-rank + compression (swap GPT model or disable if you wish)
• Fully async; safe to share a single instance across FastAPI endpoints
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from app.core.settings import env_settings

# ─────────────────────────── runtime knobs ────────────────────────────
EMBED_MODEL = env_settings.OPENAI_EMBED_MODEL
LLM_MODEL = env_settings.OPENAI_LLM_MODEL
API_KEY = env_settings.OPENAI_API_KEY
COLLECTION = env_settings.QDRANT_COLLECTION
QDRANT_URL = env_settings.QDRANT_URL
QDRANT_KEY = env_settings.QDRANT_API_KEY

MAX_PAR_EMB = 4  # parallel embed threads
EMB_CACHE = 4096  # LRU entries
TIMEOUT = 30  # Qdrant sec
RRF_K = 10  # fusion aggressiveness
DEF_TOP_K = 6
T0 = 0.0  # deterministic rerank

logger = logging.getLogger(__name__)

# ───────────────────────── embeddings (batched+cached) ────────────────
_emb = OpenAIEmbeddings(model=EMBED_MODEL, api_key=SecretStr(API_KEY))
_pool = ThreadPoolExecutor(max_workers=MAX_PAR_EMB)


async def _embed_batch(texts: Sequence[str]) -> list[list[float]]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_pool, lambda: _emb.embed_documents(list(texts)))


@lru_cache(maxsize=EMB_CACHE)
async def _embed_cached(text: str) -> list[float]:
    return (await _embed_batch([text]))[0]


# ─────────────────────────── LLM helpers ───────────────────────────────
_llm = ChatOpenAI(model=LLM_MODEL, temperature=T0, api_key=SecretStr(API_KEY))
_compressor = LLMChainExtractor.from_llm(_llm)


async def _llm_rerank(question: str, docs: list[Document], k: int) -> list[Document]:
    snippets = [d.page_content[:300].replace("\n", " ") for d in docs]
    prompt = (
        "You are a ranking assistant. Given *question* and *snippets*, "
        f"return a JSON array with the indices of the {k} most relevant snippets, best first.\n\n"
        f"Question:\n{question}\n\nSnippets:\n" + "\n".join(f"[{i}] {s}" for i, s in enumerate(snippets))
    )
    try:
        response_content = (await _llm.ainvoke(prompt)).content
        # Ensure content is a string before parsing
        if isinstance(response_content, str):
            order = json.loads(response_content)
        else:
            # If it's already structured data, use it directly
            order = response_content
        # Ensure we only use integer indices
        valid_indices = [
            int(i) for i in order if isinstance(i, int | str) and str(i).isdigit() and 0 <= int(i) < len(docs)
        ]
        return [docs[i] for i in valid_indices][:k]
    except Exception:
        logger.warning("LLM re-rank failed ➜ using raw order")
        return docs[:k]


# ─────────────────────────── main retriever ────────────────────────────
class QdrantStore:
    """Dense + sparse hybrid RAG retriever with optional LLM post-processing."""

    def __init__(self, client: AsyncQdrantClient | None = None) -> None:
        self.cli = client or AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY, timeout=TIMEOUT)
        self.col = COLLECTION
        logger.info("Retriever ready", extra={"collection": self.col})

    # ---------- helpers ----------
    async def _ensure_collection_exists(self) -> None:
        """Ensure the collection exists, create if it doesn't."""
        try:
            # Check if collection exists
            await self.cli.get_collection(env_settings.QDRANT_COLLECTION)
        except Exception:
            # Collection doesn't exist, create it
            logger.info("Creating Qdrant collection: %s", env_settings.QDRANT_COLLECTION)
            await self.cli.create_collection(
                collection_name=env_settings.QDRANT_COLLECTION,
                vectors_config=rest.VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=rest.Distance.COSINE,  # cosine similarity
                ),
                optimizers_config=rest.OptimizersConfigDiff(
                    default_segment_number=2,
                ),
                hnsw_config=rest.HnswConfigDiff(
                    payload_m=16,
                    m=0,
                ),
            )

    @staticmethod
    def _flt(user_id: str, uploads: Sequence[str]) -> rest.Filter:
        return rest.Filter(
            must=[
                rest.FieldCondition(key="user_id", match=rest.MatchValue(value=user_id)),
                rest.FieldCondition(key="upload_id", match=rest.MatchAny(any=list(uploads))),
            ]
        )

    @staticmethod
    def _doc(p: rest.ScoredPoint | tuple[str, dict]) -> Document:
        if isinstance(p, tuple):
            payload = p[1] or {}
            return Document(page_content=payload.get("content", ""), metadata=payload)
        else:
            payload = p.payload or {}
            return Document(page_content=payload.get("content", ""), metadata=payload)

    # ---------- public -----------
    async def retrieve(
        self,
        query: str,
        *,
        user_id: str,
        upload_ids: Sequence[str],
        top_k: int = DEF_TOP_K,
        rerank: bool = True,
        compress: bool = True,
    ) -> list[Document]:
        vec = await _embed_cached(query)

        # 1. Qdrant hybrid search — dense + sparse RRF (all server-side) :contentReference[oaicite:0]{index=0}
        pts = await self.cli.query_points(
            collection_name=self.col,
            prefetch=[
                rest.Prefetch(query=query, using="sparse", limit=max(32, top_k * 4)),
                rest.Prefetch(query=vec, using="dense", limit=max(32, top_k * 4)),
            ],
            query=rest.FusionQuery(fusion=rest.Fusion.RRF),
            filter=self._flt(user_id, upload_ids),
            limit=max(32, top_k * 4),
            with_payload=True,
        )
        docs = [self._doc(p) for p in pts]

        # 2. local LLM rerank (cheap, optional)
        if rerank and len(docs) > top_k:
            docs = await _llm_rerank(query, docs, k=top_k * 2)

        # 3. contextual compression (optional)
        if compress:
            docs = await _compressor.acompress_documents(documents=docs, query=query)

        return list(docs)[:top_k]

    # ---------- cleanup ----------
    async def aclose(self):
        await self.cli.close()
        _pool.shutdown(wait=False)

    async def __aenter__(self):
        await self._ensure_collection_exists()
        return self

    async def __aexit__(self, *_):
        await self.aclose()

"""
LCQdrantRetriever - async wrapper around LangChain hybrid search
────────────────────────────────────────────────────────────────
• Uses the SAME dense + SPLADE vectors your ingest writes
• One thread-pool off-loads the sync LangChain call
• Optional LLM JSON re-rank + contextual compression (unchanged)
"""

from __future__ import annotations

import json

from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from pydantic import SecretStr
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core import logging
from app.core.settings import env_settings

log = logging.get_logger(__name__)

# ─── shared resources (singletons) ─────────────────────────
CLIENT = QdrantClient(
    url=env_settings.QDRANT_URL,
    api_key=env_settings.QDRANT_API_KEY,
    prefer_grpc=True,
)

DENSE = OpenAIEmbeddings(model=env_settings.OPENAI_EMBED_MODEL, api_key=SecretStr(env_settings.OPENAI_API_KEY))
SPARSE = FastEmbedSparse(model_name="Qdrant/bm42-all-minilm-l6-v2-attentions")

LLM = ChatOpenAI(model=env_settings.OPENAI_LLM_MODEL, temperature=0.0, api_key=SecretStr(env_settings.OPENAI_API_KEY))
COMPRESSOR = LLMChainExtractor.from_llm(LLM)

# ─── main retriever class ──────────────────────────────────
class LCQdrantStore:
    def __init__(self):
        self._vs: QdrantVectorStore | None = None

    # create store lazily so startup is fast
    def _vs_lazy(self) -> QdrantVectorStore:
        if self._vs is None:
            self._vs = QdrantVectorStore(
                client=CLIENT,
                collection_name=env_settings.QDRANT_COLLECTION,
                embedding=DENSE,
                sparse_embedding=SPARSE,
                retrieval_mode=RetrievalMode.HYBRID,
                vector_name="dense",
                sparse_vector_name="sparse",
            )
        return self._vs

    # LLM JSON re-rank (same as before)
    async def _rerank(self, query: str, docs: list[Document], k: int) -> list[Document]:
        snippets = [d.page_content[:300].replace("\n", " ") for d in docs]
        prompt = (
            "You are a ranking assistant. Given *question* and *snippets*, "
            f"return a JSON array with the indices of the {k} most relevant snippets, best first.\n\n"
            f"Question:\n{query}\n\nSnippets:\n" + "\n".join(f"[{i}] {s}" for i, s in enumerate(snippets))
        )
        try:
            response = await LLM.ainvoke(prompt)
            content = response.content if isinstance(response.content, str) else str(response.content)
            order = json.loads(content)
            keep = [docs[i] for i in order if 0 <= i < len(docs)]
            return keep[:k]
        except Exception:
            log.warning("LLM rerank failed - using original order")
            return docs[:k]

    # ─── public API identical to old class ─────────────────
    async def retrieve(
        self,
        query: str,
        *,
        user_id: str,
        upload_id: str,
        top_k: int = 6,
        rerank: bool = True,
        compress: bool = True,
    ) -> list[Document]:
        vs = self._vs_lazy()
        filt = Filter(
            must=[
                FieldCondition(key="metadata.user_id", match=MatchValue(value=user_id)),
                FieldCondition(key="metadata.upload_id", match=MatchValue(value=upload_id)),
            ]
        )

        # 1) LangChain hybrid search
        # alpha controls dense-vs-sparse weight (0 => sparse-only, 1 => dense-only)
        docs = await vs.asimilarity_search(query, k=max(32, top_k * 4), filter=filt)
        log.info("Retrieved %d documents for query: %s", len(docs), query)
        if not docs:
            log.warning("No documents found for query: %s", query)
            return []

        # 2) optional LLM rerank
        if rerank and len(docs) > top_k:
            docs = await self._rerank(query, docs, k=top_k * 2)

        # 3) optional contextual compression
        if compress:
            docs = await COMPRESSOR.acompress_documents(docs, query=query)

        return list(docs[:top_k])

    # graceful shutdown for gunicorn signal hooks if you need it
    async def aclose(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

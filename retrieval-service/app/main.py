"""
Minimal async gRPC server using QdrantStore.
"""

import asyncio
import re
from collections.abc import Iterable

from grpc import aio
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.core import logging
from app.core.qdrant_store import QdrantStore
from app.core.settings import env_settings
from generated import retrieval_pb2, retrieval_pb2_grpc

logging.configure_logging()
log = logging.get_logger(__name__)
_store = QdrantStore()

# ---------------- routing heuristic ------------------------------------------
_KEYWORDY = re.compile(r"\b(sec|§|error)\b|\d{4,}", re.I)


def _decide(query: str) -> str:
    if _KEYWORDY.search(query):
        return "fulltext"
    if len(query.split()) <= 3:
        return "hybrid"
    return "vector"


# ---------------- gRPC servicer ----------------------------------------------
class RetrievalServicer(retrieval_pb2_grpc.RetrievalServiceServicer):
    async def Search(self, request, context):
        mode = request.search_type or _decide(request.query)
        docs = await _store.search(
            request.user_id,
            list(request.upload_ids),
            request.query,
            max(1, request.top_k or 4),
            request.score_threshold,
            mode,
        )

        results: Iterable[retrieval_pb2.SearchResult] = (  # type: ignore
            retrieval_pb2.SearchResult(  # type: ignore
                content=d.page_content,
                metadata={k: str(v) for k, v in d.metadata.items()},
                score=float(d.metadata.get("score", 0.0)),
            )
            for d in docs
        )
        return retrieval_pb2.SearchResponse(  # type: ignore
            results=list(results),
            total=len(docs),
            query=request.query,
            search_type=mode,
        )


# ---------------- server bootstrap -------------------------------------------
async def serve():
    server = aio.server()
    retrieval_pb2_grpc.add_RetrievalServiceServicer_to_server(RetrievalServicer(), server)

    hs = health.HealthServicer()
    hs.set("", health_pb2.HealthCheckResponse.SERVING)
    hs.set("retrieval.RetrievalService", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(hs, server)

    addr = f"0.0.0.0:{env_settings.GRPC_PORT}"
    server.add_insecure_port(addr)
    log.info("gRPC listening at %s", addr)

    try:
        await server.start()
        await server.wait_for_termination()
    finally:
        await _store.close()
        log.info("Service stopped")


if __name__ == "__main__":
    asyncio.run(serve())

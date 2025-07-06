"""
retrieval-service  –  minimal async gRPC server with Qdrant backend
───────────────────────────────────────────────────────────────────
• RPC     : RetrievalService/Search
• Health  : grpc.health.v1.Health/Check
"""

from __future__ import annotations

import asyncio
import re
import signal
from collections.abc import Iterable

from grpc import aio
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.core import logging
from app.core.qdrant_store import QdrantStore
from app.core.settings import env_settings
from generated import retrieval_pb2, retrieval_pb2_grpc

# ─────────── setup logging & store ───────────────────────────────────────────
logging.configure_logging()
log = logging.get_logger(__name__)
_store = QdrantStore()

# ─────────── simple routing heuristic ───────────────────────────────────────
_KEYWORDY = re.compile(r"\b(sec|§|error)\b|\d{4,}", re.I)


def _decide(query: str) -> str:
    if _KEYWORDY.search(query):
        return "fulltext"
    if len(query.split()) <= 3:
        return "hybrid"
    return "vector"


# ─────────── gRPC servicer ───────────────────────────────────────────────────
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

        results: Iterable[retrieval_pb2.SearchResult] = (
            retrieval_pb2.SearchResult(
                content=d["content"],
                metadata={k: str(v) for k, v in d["metadata"].items()},
                score=float(d["metadata"].get("score", 0.0)),
            )
            for d in docs
        )
        return retrieval_pb2.SearchResponse(
            results=list(results),
            total=len(docs),
            query=request.query,
            search_type=mode,
        )


# ─────────── server bootstrap ────────────────────────────────────────────────
async def serve() -> None:
    server = aio.server()
    retrieval_pb2_grpc.add_RetrievalServiceServicer_to_server(RetrievalServicer(), server)

    # health
    hs = health.HealthServicer()
    hs.set("", health_pb2.HealthCheckResponse.SERVING)
    hs.set("retrieval.RetrievalService", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(hs, server)

    addr = f"0.0.0.0:{env_settings.GRPC_PORT}"
    server.add_insecure_port(addr)
    log.info("gRPC listening at %s", addr)

    # graceful shutdown on SIGINT / SIGTERM
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await server.start()
    await stop_event.wait()  # block until signal arrives
    await server.stop(grace=5)  # allow in-flight RPCs
    await _store.close()
    log.info("Service stopped")


if __name__ == "__main__":
    asyncio.run(serve())

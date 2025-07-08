# main.py  –  async gRPC retrieval-service (Fast, Hybrid)
# ───────────────────────────────────────────────────────
# RPC    : retrieval.RetrievalService/Search
# Health : grpc.health.v1.Health/Check
# ───────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import signal
from collections.abc import Iterable

from grpc import aio
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.core import logging
from app.core.qdrant_store import LCQdrantStore
from app.core.settings import env_settings
from generated import retrieval_pb2, retrieval_pb2_grpc

# ──────── logging ───────────────────────────────────────
logging.configure_logging()
log = logging.get_logger(__name__)


# ──────── gRPC servicer ─────────────────────────────────
class RetrievalServicer(retrieval_pb2_grpc.RetrievalServiceServicer):
    def __init__(self, retriever: LCQdrantStore) -> None:
        self.retriever = retriever

    async def Search(self, request, context):
        docs = await self.retriever.retrieve(
            query=request.query,
            user_id=request.user_id,
            upload_id=request.upload_id,
            top_k=max(1, request.top_k or 4),
            rerank=True,
            compress=True,
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
        )

# ──────── server bootstrap ──────────────────────────────
async def serve() -> None:
    retriever = LCQdrantStore()
    server = aio.server()

    retrieval_pb2_grpc.add_RetrievalServiceServicer_to_server(RetrievalServicer(retriever), server)

    # Health
    hs = health.HealthServicer()
    hs.set("", health_pb2.HealthCheckResponse.SERVING)
    hs.set("retrieval.RetrievalService", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(hs, server)

    addr = f"0.0.0.0:{env_settings.GRPC_PORT}"
    server.add_insecure_port(addr)
    log.info("gRPC service listening at %s", addr)

    # graceful shutdown
    stop_evt = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_evt.set)

    await server.start()
    await stop_evt.wait()
    await server.stop(grace=5)
    await retriever.aclose()
    log.info("gRPC service stopped")

if __name__ == "__main__":
    asyncio.run(serve())

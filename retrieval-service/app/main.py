# main.py  –  minimal async gRPC retrieval-service
# ────────────────────────────────────────────────
# RPC    : retrieval.RetrievalService/Search
# Health : grpc.health.v1.Health/Check
# ────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import signal
from collections.abc import Iterable

from grpc import aio
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.core import logging
from app.core.qdrant_store import QdrantStore
from app.core.settings import env_settings
from generated import retrieval_pb2, retrieval_pb2_grpc

# ─────────── log & misc ─────────────────────────
logging.configure_logging()
logger = logging.get_logger(__name__)


# ─────────── gRPC servicer ──────────────────────
class RetrievalServicer(retrieval_pb2_grpc.RetrievalServiceServicer):
    def __init__(self, store: QdrantStore):
        self.store = store  # inject retriever instance

    async def Search(self, request, context):
        # 1. call QdrantStore.retrieve -----------------------------
        docs = await self.store.retrieve(
            query=request.query,
            user_id=request.user_id,
            upload_ids=list(request.upload_ids),
            top_k=max(1, request.top_k or 4),
            rerank=True,  # or False if you want pure DB scores
            compress=True,
        )

        # 2. marshal docs → protobuf -------------------------------
        results: Iterable[retrieval_pb2.SearchResult] = (  # type: ignore
            retrieval_pb2.SearchResult(  # type: ignore
                content=d.page_content,
                metadata={k: str(v) for k, v in d.metadata.items()},
                score=float(d.metadata.get("score", 0.0)),  # may be missing
            )
            for d in docs
        )

        return retrieval_pb2.SearchResponse(  # type: ignore
            results=list(results),
            total=len(docs),
            query=request.query,
        )


# ─────────── server bootstrap / graceful shutdown ────────────────────
async def serve() -> None:
    store = QdrantStore()  # create once
    server = aio.server()
    retrieval_pb2_grpc.add_RetrievalServiceServicer_to_server(RetrievalServicer(store), server)

    # Health service
    hs = health.HealthServicer()
    hs.set("", health_pb2.HealthCheckResponse.SERVING)
    hs.set("retrieval.RetrievalService", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(hs, server)

    addr = f"0.0.0.0:{env_settings.GRPC_PORT}"
    server.add_insecure_port(addr)
    logger.info("gRPC listening at %s", addr)

    # graceful-shutdown on SIGINT/SIGTERM
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await server.start()
    await stop_event.wait()  # block until we get ^C / docker stop
    await server.stop(grace=5)
    await store.aclose()  # close Qdrant client + thread-pool
    logger.info("Service stopped")


if __name__ == "__main__":
    asyncio.run(serve())

from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.memory.checkpoint import AsyncPostgresCheckpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await AsyncPostgresCheckpoint.setup_async()
    yield

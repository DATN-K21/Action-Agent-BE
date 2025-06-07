import socket
from contextlib import asynccontextmanager
from pathlib import Path

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI
from alembic import command
from alembic.config import Config

from app.core import logging
from app.memory.checkpoint import AsyncPostgresPool

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Manually set up the PostgreSQL connection pool
        await AsyncPostgresPool.asetup()

        # Setup PostgreSQL migrations using Alembic
        alembic_cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")

        # Manually resolve dependencies at startup
        # checkpointer = await get_checkpointer()

        yield
    finally:
        await AsyncPostgresPool.atear_down()

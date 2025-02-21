import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.core import logging
from app.memory.checkpoint import AsyncPostgresCheckpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logging.configure_logging()
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
        await AsyncPostgresCheckpoint.setup_async()
        yield
    finally:
        await AsyncPostgresCheckpoint.teardown_async()

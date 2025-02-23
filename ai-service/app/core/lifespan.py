import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.memory.checkpoint import AsyncPostgresPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
        await AsyncPostgresPool.asetup()
        yield
    finally:
        await AsyncPostgresPool.atear_down()

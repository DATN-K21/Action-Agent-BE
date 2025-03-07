import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.core.graph.deps import get_extension_builder_manager
from app.core.socketio import sio_asgi
from app.memory.checkpoint import AsyncPostgresPool
from app.memory.deps import get_checkpointer
from app.services.extensions.deps import get_extension_service_manager, get_gmail_service, get_google_calendar_service
from app.sockets.extension_socket import ExtensionNamespace


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Manually set up and tear down the connection
        await AsyncPostgresPool.asetup()

        # Manually resolve dependencies at startup
        checkpointer = await get_checkpointer()
        extension_builder_manager = get_extension_builder_manager(checkpointer)
        extension_service_manager = get_extension_service_manager(
            gmail_service=get_gmail_service(),
            google_calendar_service=get_google_calendar_service(),
        )
        sio_asgi.register_namespace(
            ExtensionNamespace(
                namespace="/extension",
                builder_manager=extension_builder_manager,
                extension_service_manager=extension_service_manager
            )
        )
        yield
    finally:
        await AsyncPostgresPool.atear_down()

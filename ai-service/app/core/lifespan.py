import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.core import logging
from app.core.graph.deps import get_extension_builder_manager
from app.core.session import engine
from app.core.socketio import get_socketio_server
from app.memory.checkpoint import AsyncPostgresPool, get_checkpointer
from app.models.base_entity import Base
from app.services.extensions.deps import (
    get_extension_service_manager,
    get_gmail_service,
    get_google_calendar_service,
    get_google_drive_service,
    get_google_maps_service,
    get_google_meet_service,
    get_notion_service,
    get_outlook_service,
    get_slack_service,
    get_youtube_service,
)
from app.sockets.extension_socket import ExtensionNamespace

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Manually set up the PostgreSQL connection pool
        await AsyncPostgresPool.asetup()

        # Setup PostgreSQL migrations
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info(f"SQLAlchemy tables: {Base.metadata.tables.keys()}")
            logger.info("SQLAlchemy tables created")

        # Manually resolve dependencies at startup
        checkpointer = await get_checkpointer()
        extension_builder_manager = get_extension_builder_manager(checkpointer)
        extension_service_manager = get_extension_service_manager(
            gmail_service=get_gmail_service(),
            google_calendar_service=get_google_calendar_service(),
            google_meet_service=get_google_meet_service(),
            google_maps_service=get_google_maps_service(),
            youtube_service=get_youtube_service(),
            slack_service=get_slack_service(),
            outlook_service=get_outlook_service(),
            google_drive_service=get_google_drive_service(),
            notion_service=get_notion_service(),
        )

        get_socketio_server().register_namespace(
            ExtensionNamespace(
                namespace="/extension",
                builder_manager=extension_builder_manager,
                extension_service_manager=extension_service_manager,
            )
        )

        yield
    finally:
        await AsyncPostgresPool.atear_down()

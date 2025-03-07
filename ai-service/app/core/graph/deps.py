from functools import lru_cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.graph.base import GraphBuilder
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.memory.deps import get_checkpointer


@lru_cache()
def get_extension_builder_manager(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = ExtensionBuilderManager()

    # Register gmail graph builder
    gmail_builder = GraphBuilder(
        checkpointer=checkpointer,
        name="gmail"
    )
    manager.register_extension_builder(gmail_builder)

    # Register google calendar graph builder
    google_calendar_builder = GraphBuilder(checkpointer=checkpointer, name="google-calendar")
    manager.register_extension_builder(google_calendar_builder)

    # Register google meet graph builder
    google_meet_builder = GraphBuilder(checkpointer=checkpointer, name="google-meet")
    manager.register_extension_builder(google_meet_builder)

    return manager
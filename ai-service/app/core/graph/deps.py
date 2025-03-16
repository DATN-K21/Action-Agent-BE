from functools import lru_cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.graph.base import GraphBuilder
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.memory.deps import get_checkpointer
from app.services.extensions.deps import get_gmail_service, get_google_calendar_service, get_google_meet_service, \
    get_google_maps_service, get_youtube_service, get_slack_service, get_outlook_service


@lru_cache()
def get_extension_builder_manager(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = ExtensionBuilderManager()

    # Register gmail graph builder
    gmail_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_gmail_service().get_name(),
    )
    manager.register_extension_builder(gmail_builder)

    # Register google calendar graph builder
    google_calendar_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_google_calendar_service().get_name()
    )
    manager.register_extension_builder(google_calendar_builder)

    # Register google meet graph builder
    google_meet_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_google_meet_service().get_name()
    )
    manager.register_extension_builder(google_meet_builder)

    # Register google map graph builder
    google_map_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_google_maps_service().get_name()
    )
    manager.register_extension_builder(google_map_builder)

    # Register youtube graph builder
    youtube_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_youtube_service().get_name()
    )
    manager.register_extension_builder(youtube_builder)

    #Register slack graph builder
    slack_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_slack_service().get_name()
    )
    manager.register_extension_builder(slack_builder)

    #Register outlook graph builder
    outlook_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_outlook_service().get_name()
    )
    manager.register_extension_builder(outlook_builder)

    return manager

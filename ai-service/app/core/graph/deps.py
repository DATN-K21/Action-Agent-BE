from functools import lru_cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from structlog import BoundLogger

from app.core.agents.agent import Agent
from app.core.cache.cached_agents import AgentCache
from app.core.graph.base import GraphBuilder
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.memory.checkpoint import get_checkpointer
from app.services.extensions.deps import (
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
from app.services.extensions.extension_service_manager import ExtensionServiceManager


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

    # Register slack graph builder
    slack_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_slack_service().get_name()
    )
    manager.register_extension_builder(slack_builder)

    # Register outlook graph builder
    outlook_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_outlook_service().get_name()
    )
    manager.register_extension_builder(outlook_builder)

    # Register google drive graph builder
    google_drive_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_google_drive_service().get_name()
    )
    manager.register_extension_builder(google_drive_builder)

    # Register notion graph builder
    notion_builder = GraphBuilder(
        checkpointer=checkpointer,
        name=get_notion_service().get_name()
    )
    manager.register_extension_builder(notion_builder)

    return manager


def create_extension(
        extension_name: str,
        user_id: str,
        extension_service_manager: ExtensionServiceManager,
        builder_manager: ExtensionBuilderManager,
        logger: BoundLogger
):
    extension_service = extension_service_manager.get_extension_service(extension_name)
    builder_manager.update_builder_tools(
        builder_name=extension_name,
        tools=extension_service.get_authed_tools(user_id),  # type: ignore
    )

    builder = builder_manager.get_extension_builder(extension_name)

    if builder is None:
        logger.error("Builder not found")
        return None

    graph = builder.build_graph(perform_action=True, has_human_acceptance_flow=True)
    return Agent(graph)


def get_extension(
        extension_name: str,
        user_id: str,
        agent_cache: AgentCache,
        extension_service_manager: ExtensionServiceManager,
        builder_manager: ExtensionBuilderManager,
        logger: BoundLogger
):
    agent = agent_cache.get(user_id=user_id, agent_type=extension_name)
    if agent is None:
        agent = create_extension(
            extension_name=extension_name,
            user_id=user_id,
            extension_service_manager=extension_service_manager,
            builder_manager=builder_manager,
            logger=logger,
        )
        if agent is None:
            raise ValueError("Invalid extension name")

    agent_cache.set(user_id=user_id, agent_type=extension_name, agent=agent)

    return agent

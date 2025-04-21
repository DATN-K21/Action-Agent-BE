from fastapi import APIRouter, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import ensure_user_id
from app.core import logging
from app.core.cache.cached_mcp_agents import McpAgentCache, get_mcp_agent_cache
from app.core.graph.v2.mcp_agent import get_mcp_agent
from app.core.session import get_db_session
from app.core.utils.config_helper import get_invocation_config
from app.memory.checkpoint import get_checkpointer
from app.models import Thread
from app.schemas.base import ResponseWrapper
from app.schemas.mcp_agent import McpResponse, McpRequest
from app.services.database.connected_mcp_service import ConnectedMcpService, get_connected_mcp_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/mcp-agent", tags=["API-V2 | MCP Agent"])


# @router.get(path="/{user_id}/get-all", summary="Get the list mcps of a user.",
#             response_model=ResponseWrapper[GetExtensionsResponse])
# async def get_user_mcps(
#         user_id: str,
#         extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
#         _: bool = Depends(ensure_authenticated),
# ):
#     try:
#         extensions = extension_service_manager.get_all_extension_service_names()
#         response_data = GetExtensionsResponse(extensions=extensions)
#         return ResponseWrapper.wrap(status=200, data=response_data).to_response()
#     except Exception as e:
#         logger.error(f"Has error: {str(e)}", exc_info=True)
#         return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
#
#
# @router.get(path="/{user_id}/{connected_mcp_id}/get-actions", summary="Get actions available for extension.",
#             response_model=ResponseWrapper[GetActionsResponse])
# async def get_actions(
#         user_id: str,
#         connected_mcp_id: str,
#         extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
#         _: bool = Depends(ensure_authenticated),
# ):
#     try:
#         # 1. Get the extension service
#         extension_service = extension_service_manager.get_extension_service(extension_name)
#         if extension_service is None:
#             return ResponseWrapper.wrap(status=404, message="Extension not found").to_response()
#
#         # 2. Get the actions from the extension service
#         extension_service.get_actions()
#         actions = extension_service.get_action_names()
#         response_data = GetActionsResponse(actions=list(actions))
#         return ResponseWrapper.wrap(status=200, data=response_data).to_response()
#
#     except Exception as e:
#         logger.error(f"Error fetching actions: {str(e)}", exc_info=True)
#         return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/chat/{user_id}/{thread_id}", summary="Chat with the mcp agent.",
             response_model=ResponseWrapper[McpResponse])
async def chat(
        user_id: str,
        thread_id: str,
        request: McpRequest,
        mcp_agent_cache: McpAgentCache = Depends(get_mcp_agent_cache),
        connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        db: AsyncSession = Depends(get_db_session),
        _: bool = Depends(ensure_user_id),
):
    try:
        # Check the thread
        stmt = (
            select(Thread.id)
            .where(
                Thread.user_id == user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )
        db_thread = (await db.execute(stmt)).scalar_one_or_none()
        if db_thread is None:
            return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()

        agent, client = await get_mcp_agent(
            user_id=user_id,
            mcp_agent_cache=mcp_agent_cache,
            connected_mcp_service=connected_mcp_service,
            checkpointer=checkpointer
        )

        config = get_invocation_config(
            thread_id=thread_id,
            recursion_limit=request.max_recursion,
        )

        response = await agent.ainvoke(
            input={"messages": [request.input]},
            config=config
        )

        return ResponseWrapper.wrap(
            status=200,
            data=McpResponse(
                user_id=user_id,
                thread_id=thread_id,
                output=response["messages"][-1].content
            )
        ).to_response()

    except Exception as e:
        logger.error(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

# from fastapi import APIRouter, Depends
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.api.auth import ensure_user_id
# from app.core import logging
# from app.core.graph.v2.multi_agent import acreate_multi_agent
# from app.core.session import get_db_session
# from app.core.utils.config_helper import create_invocation_config
# from app.memory.checkpoint import get_checkpointer
# from app.db_models.thread import Thread
# from app.schemas.agent import AgentChatRequest, AgentChatResponse
# from app.schemas.base import ResponseWrapper
# from app.services.database.assistant_service import AssistantService, get_assistant_service
# from app.services.database.extension_assistant_service import ExtensionAssistantService, get_extension_assistant_service
# from app.services.database.mcp_assistant_service import McpAssistantService, get_mcp_assistant_service
# from app.services.extensions.deps import get_extension_service_manager
# from app.services.extensions.extension_service_manager import ExtensionServiceManager
#
# logger = logging.get_logger(__name__)
#
# router = APIRouter(prefix="/multi-agent", tags=["Multi Agent"])
#
#
# @router.post("/chat/{user_id}/{assistant_id}/{thread_id}", summary="Chat with the agent.",
#              response_model=ResponseWrapper[AgentChatResponse])
# async def chat(
#         user_id: str,
#         assistant_id: str,
#         thread_id: str,
#         request: AgentChatRequest,
#         checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
#         db: AsyncSession = Depends(get_db_session),
#         assistant_service: AssistantService = Depends(get_assistant_service),
#         extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
#         mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
#         extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
#         _: bool = Depends(ensure_user_id),
# ):
#     try:
#         # Check the thread
#         stmt = (
#             select(Thread.id)
#             .where(
#                 Thread.user_id == user_id,
#                 Thread.id == thread_id,
#                 Thread.is_deleted.is_(False),
#             )
#             .limit(1)
#         )
#         db_thread = (await db.execute(stmt)).scalar_one_or_none()
#         if db_thread is None:
#             return ResponseWrapper.wrap(status=404, message="Thread not found").to_response()
#
#         multi_agent = await acreate_multi_agent(
#             user_id=user_id,
#             assistant_id=assistant_id,
#             checkpointer=checkpointer,
#             assistant_service=assistant_service,
#             extension_assistant_service=extension_assistant_service,
#             mcp_assistant_service=mcp_assistant_service,
#             extension_service_manager=extension_service_manager,
#         )
#
#         config = create_invocation_config(
#             thread_id=thread_id,
#             recursion_limit=request.recursion_limit,
#         )
#
#         # Chat with the agent
#         response = await multi_agent.ainvoke(
#             input={"messages": [request.input], "question": request.input},
#             config=config
#         )
#
#         return ResponseWrapper.wrap(
#             status=200,
#             data=AgentChatResponse(
#                 thread_id=thread_id,
#                 output=response["messages"][-1].content,  # type: ignore
#             ),
#         ).to_response()
#
#     except Exception as e:
#         logger.exception("Has error: %s", str(e))
#         return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

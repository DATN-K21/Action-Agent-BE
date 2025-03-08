from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.core.utils.streaming import to_sse
from app.schemas.agent import AgentRequest, AgentResponse, GetAgentsResponse
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter()


@router.get("/get-all", summary="Endpoint to get all agent names.", response_model=ResponseWrapper[GetAgentsResponse])
async def get_agents(
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    try:
        agents = agent_manager.get_all_agent_names()
        response_data = GetAgentsResponse(agent_names=list(agents))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/chat", summary="Endpoint to chat with the agent.", response_model=ResponseWrapper[AgentResponse])
async def execute(
    request: AgentRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    try:
        agent = agent_manager.get_agent(name=request.agent_name)

        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        response = await agent.async_chat(
            question=request.input,
            thread_id=request.thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

        return ResponseWrapper.wrap(
            status=200,
            data=AgentResponse(
                thread_id=request.thread_id,
                output=response.output,  # type: ignore
            ),
        ).to_response()

    except Exception as e:
        logger.error(f"Error in executing Gmail API: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/stream", summary="Endpoint to stream with the agent.", response_class=EventSourceResponse)
async def stream(
    request: AgentRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    try:
        agent = agent_manager.get_agent(name=request.agent_name)

        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        response = await agent.async_stream(
            question=request.input,
            thread_id=request.thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

        return EventSourceResponse(to_sse(response))

    except Exception as e:
        logger.error(f"Error executing Gmail API: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

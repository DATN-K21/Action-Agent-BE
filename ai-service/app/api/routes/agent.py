from sys import exc_info

from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.core import logging
from app.core.agents.agent_manager import AgentManager
from app.core.agents.deps import get_agent_manager
from app.schemas.base import ResponseWrapper
from app.schemas.agent import AgentResponse, AgentRequest, GetAgentsResponse
from app.utils.streaming import to_sse

logger = logging.get_logger(__name__)


router = APIRouter()


@router.get("/all", tags=["Agent"], description="Endpoint to get all agent names.")
async def get_agents(
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    try:
        agents = agent_manager.get_all_agent_names()
        response_data = GetAgentsResponse(agent_names=list(agents))
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/chat")
async def execute(
    request: AgentRequest,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    try:
        agent = agent_manager.get_agent(name=request.agent_name)

        if agent is None:
            return ResponseWrapper.wrap(status=404, message="Agent not found").to_response()

        response = await agent.async_execute(
            question=request.input,
            thread_id=request.thread_id,
            max_recursion=request.recursion_limit if request.recursion_limit is not None else 5,
        )

        return ResponseWrapper.wrap(status=200, data=AgentResponse(
            thread_id=request.thread_id,
            output=response.output,
        )).to_response()

    except Exception as e:
        logger.error(f"Error in executing Gmail API: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/stream")
async def stream(
    request: AgentRequest,
    agent_manager: AgentManager = Depends(get_agent_manager)
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

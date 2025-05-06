from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class AgentChatRequest(BaseRequest):
    input: str = Field(min_length=1, max_length=8000, title="Input", examples=["Hello!"])
    recursion_limit: Optional[int] = Field(None, ge=1, le=50, title="Recursion Limit", examples=[20])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class AgentResponse(BaseResponse):
    thread_id: str = Field(..., title="Thread ID", examples=["abcdef"])
    output: str = Field(..., title="Output", examples=["Hello!"])


class GetAgentsResponse(BaseResponse):
    agent_names: list[str] = Field(title="Agent Names", examples=[["chat-agent", "email-agent"]])


class AgentChatResponse(BaseResponse):
    thread_id: str = Field(..., title="Thread ID", examples=["abcdef"])
    output: Optional[str] = Field(None, title="Output", examples=["Hello!"])


class GetAgentV2Response(BaseResponse):
    name: str = Field(..., title="Agent Name", examples=["chat-agent"])
    description: Optional[str] = Field(None, title="Description", examples=["Chat agent"])
    image_url: Optional[str] = Field(None, title="Image URL", examples=["http://example.com/image.png"])
    tools: Optional[list[str]] = Field(None, title="Tools", examples=[["tool1", "tool2"]])
    child_agents: Optional[list[str]] = Field(None, title="Child Agents", examples=[["child-agent1", "child-agent2"]])
    is_public: Optional[bool] = Field(None, title="Is Public", examples=[True])


class GetAgentV2ListResponse(BaseResponse):
    agents: list[GetAgentV2Response] = Field(..., title="Agents", examples=[[
        {
            "name": "chat-agent",
            "description": "Chat agent",
            "image_url": "http://example.com/image.png",
            "tools": ["tool1", "tool2"],
            "child_agents": ["child-agent1", "child-agent2"],
            "is_public": True
        }
    ]])
